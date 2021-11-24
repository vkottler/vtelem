"""
vtelem - A module implementing a message storage.
"""

# built-in
from contextlib import contextmanager
import os
from tempfile import TemporaryDirectory
from typing import Callable, Dict, Iterator, List, Optional, Tuple

# internal
from vtelem.classes.data_cache import DataCache
from vtelem.frame.fields import to_parsed
from vtelem.types.frame import FrameType, MessageType, ParsedFrame

MessageCallback = Callable[[MessageType, int, bytes], None]
CallbackMap = Dict[MessageType, List[MessageCallback]]


class MessageDispatcher:
    """
    A class managing callback routines associated with given message types.
    """

    def __init__(self, initial_callbacks: CallbackMap = None) -> None:
        """Construct a new message dispatcher."""

        if initial_callbacks is None:
            initial_callbacks = {}
        self.message_callbacks: CallbackMap = initial_callbacks

        for mtype in MessageType:
            if mtype not in self.message_callbacks:
                self.message_callbacks[mtype] = []

    def add_callback(
        self, mtype: MessageType, callback: MessageCallback
    ) -> None:
        """
        Add a callback to consume a specific message type when complete
        messages are received.
        """

        self.message_callbacks[mtype].append(callback)

    def service_callbacks(
        self, mtype: MessageType, number: int, data: bytes
    ) -> None:
        """Invoke callbacks for a message."""

        for callback in self.message_callbacks[mtype]:
            callback(mtype, number, data)


class MessageCache(DataCache, MessageDispatcher):
    """
    A class for ingesting message frames so they can be accessed as fully
    coherent messages when completely received.
    """

    def __init__(
        self, cache_dir: str, initial_callbacks: CallbackMap = None
    ) -> None:
        """Construct a new message cache."""

        DataCache.__init__(self, cache_dir)
        MessageDispatcher.__init__(self, initial_callbacks)

        self.fragment_data: dict = {}
        self.fragment_dir = cache_dir + "_fragments"

        for mtype in MessageType:
            mtype_str = str(mtype.value)
            if mtype_str not in self.data:
                self.data[mtype_str] = {}
            self.fragment_data[mtype.value] = {}

        self.load_fragments(self.fragment_dir)
        self.service_all_callbacks()

    def service_all_callbacks(self) -> None:
        """Invoke registered callbacks for all complete messages."""

        for mtype in MessageType:
            callbacks = self.message_callbacks[mtype]
            for crc in self.complete(mtype):
                message = self.content(mtype, crc)
                assert message is not None
                for callback in callbacks:
                    callback(mtype, message[0], message[1])

    def load_fragments(self, fragment_dir: str) -> None:
        """Load fragment data from disk."""

        os.makedirs(fragment_dir, exist_ok=True)

        # load data for every message type
        for mtype in os.listdir(fragment_dir):
            type_data = self.fragment_data[int(mtype)]
            curr = os.path.join(fragment_dir, mtype)

            # load data for all crc's from this message type
            for crc in os.listdir(curr):
                crc_int = int(crc)
                if crc_int not in type_data:
                    type_data[crc_int] = {}
                crc_data = type_data[crc_int]
                curr = os.path.join(curr, crc)

                # load all fragments for this message's crc
                for fragment in os.listdir(curr):
                    with open(os.path.join(curr, fragment), "rb") as frag:
                        crc_data[int(fragment)] = frag.read()

    def store_fragment(
        self, mtype: MessageType, crc: int, fragment_index: int, data: bytes
    ) -> None:
        """Store a message fragment to disk."""

        # store data
        to_write = self.fragment_data[mtype.value]
        if crc not in to_write:
            to_write[crc] = {}
        to_write = to_write[crc]
        to_write[fragment_index] = data

        # write data to disk
        path = os.path.join(self.fragment_dir, str(mtype.value), str(crc))
        os.makedirs(path, exist_ok=True)
        path = os.path.join(path, str(fragment_index))
        with open(path, "wb") as frag:
            frag.write(data)

    def complete(self, mtype: MessageType) -> List[int]:
        """Get complete messages (by checksum) for a given type."""

        result = []
        for crc, data in self.data[str(mtype.value)].items():
            if data["complete"]:
                result.append(int(crc))
        return result

    def content(
        self, mtype: MessageType, crc: int
    ) -> Optional[Tuple[int, bytes]]:
        """
        Get the contents of a message (by type and checksum) if it's complete.
        """

        type_data = self.data[str(mtype.value)]
        crc_str = str(crc)
        if crc_str not in type_data or not type_data[crc_str]["complete"]:
            return None

        message = type_data[crc_str]
        fragments = self.fragment_data[mtype.value][crc]

        # combine fragments
        data = bytearray()
        for i in range(message["fragments"]):
            data += fragments[i]

        return message["number"], data

    def content_str(
        self, mtype: MessageType, crc: int
    ) -> Optional[Tuple[int, str]]:
        """
        Get the String contents of a message (by type and checksum) if it's
        complete.
        """

        result = self.content(mtype, crc)
        if result is None:
            return result
        return result[0], result[1].decode()

    def ingest(self, frame: ParsedFrame) -> None:
        """Ingest an arbitrary message frame."""

        assert frame.header.type == FrameType.MESSAGE
        message = to_parsed(frame.body)

        # get data for this message type
        type_data = self.data[str(message.type.value)]

        # get data for this message's crc
        crc_str = str(message.crc)
        if crc_str not in type_data:
            type_data[crc_str] = {"fragments": 0, "complete": False}
        crc_data = type_data[crc_str]

        # if we already have all of the fragments, don't process this frame
        # further
        if crc_data["complete"]:
            crc_data["number"] = message.number
            return

        # store this message fragment if we don't have it
        if message.fragment_index not in crc_data:
            self.store_fragment(
                message.type, message.crc, message.fragment_index, message.data
            )
            crc_data["fragments"] += 1

            # mark this message as complete if we now have all of the fragments
            if crc_data["fragments"] == message.total_fragments:
                crc_data["complete"] = True
                crc_data["number"] = message.number

                # service message consumers
                full_message = self.content(message.type, message.crc)
                assert full_message is not None
                self.service_callbacks(
                    message.type, full_message[0], full_message[1]
                )


@contextmanager
def from_temp_dir(
    initial_callbacks: CallbackMap = None,
) -> Iterator[MessageCache]:
    """Create a message cache using a temporary directory."""

    with TemporaryDirectory() as cache_dir:
        yield MessageCache(cache_dir, initial_callbacks)
