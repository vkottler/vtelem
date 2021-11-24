"""
vtelem - A module for building frames of channel data from emissions.
"""

# built-in
import logging
from queue import Queue
from typing import List, Tuple

# internal
from vtelem.channel import Channel
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.event_queue import EventQueue
from vtelem.classes.time_entity import OptionalRLock
from vtelem.enums.primitive import Primitive
from vtelem.frame import Frame
from vtelem.frame.channel import ChannelFrame
from vtelem.frame.framer import Framer
from vtelem.frame.framer import build_dummy_frame as dummy_frame

LOG = logging.getLogger(__name__)


class ChannelFramer(Framer):
    """
    An extension of channel management that builds frames from emitted data.
    """

    def __init__(
        self,
        mtu: int,
        registry: ChannelRegistry,
        channels: List[Channel],
        channel_lock: OptionalRLock,
        app_id_basis: float = None,
        use_crc: bool = True,
    ) -> None:
        """Construct a new channel framer."""

        super().__init__(mtu, app_id_basis, use_crc)
        self.registry = registry
        self.channels = channels
        self.lock = channel_lock

    def new_event_frame(self, time: float = None) -> ChannelFrame:
        """Construct a new event-frame object."""

        frame = self.new_frame("event", time)
        assert isinstance(frame, ChannelFrame)
        return frame

    def new_data_frame(self, time: float = None) -> ChannelFrame:
        """Construct a new data-frame object."""

        frame = self.new_frame("data", time)
        assert isinstance(frame, ChannelFrame)
        return frame

    def add_channel(self, channel: Channel) -> None:
        """Add another managed channel."""

        self.channels.append(channel)

    def build_event_frames(
        self,
        time: float,
        event_queue: EventQueue,
        queue: Queue,
        write_crc: bool = True,
    ) -> Tuple[int, int]:
        """
        Consume the current event queue and build frames from the contained
        events.
        """

        frame_count = 0
        events = event_queue.consume()
        event_count = len(events)

        curr_frame = self.new_event_frame(time)
        for event in events:
            chan_id = self.registry.get_id(event[0])
            assert chan_id is not None
            chan_type = self.registry.get_channel_type(chan_id)

            # add this event, start a new frame if necessary
            if not curr_frame.add_event(
                chan_id, chan_type, event[1], event[2]
            ):
                curr_frame.finalize(write_crc and self.use_crc)
                queue.put(curr_frame)
                frame_count += 1
                curr_frame = self.new_event_frame()
                assert curr_frame.add_event(
                    chan_id, chan_type, event[1], event[2]
                )

        # finalize the last frame if necessary
        if event_count and not curr_frame.finalized:
            curr_frame.finalize(write_crc and self.use_crc)
            queue.put(curr_frame)
            frame_count += 1

        return (frame_count, event_count)

    def build_data_frames(
        self, time: float, queue: Queue, write_crc: bool = True
    ) -> Tuple[int, int]:
        """
        For this step, gather up channel emissions into discrete frames for
        wire-level transport.
        """

        frame_count = 0
        emit_count = 0

        curr_frame = self.new_data_frame(time)
        with self.lock:
            for channel in self.channels:
                result = channel.emit(time)

                # if the channel emitted, add it to the current frame
                if result is not None:
                    emit_count += 1
                    chan_id = self.registry.get_id(channel.name)
                    assert chan_id is not None

                    # if we failed to add this emit to the current frame,
                    # finalize it and start a new one
                    if not curr_frame.add(chan_id, channel.type, result):
                        curr_frame.finalize(write_crc and self.use_crc)
                        queue.put(curr_frame)
                        frame_count += 1
                        curr_frame = self.new_data_frame()
                        assert curr_frame.add(chan_id, channel.type, result)

        # finalize the last frame if necessary
        if emit_count and not curr_frame.finalized:
            curr_frame.finalize(write_crc and self.use_crc)
            queue.put(curr_frame)
            frame_count += 1

        return (frame_count, emit_count)


def build_dummy_frame(
    overall_size: int, app_id_basis: float = None, bad_crc: bool = False
) -> Frame:
    """Build an empty frame of a specified size."""

    def frame_builder(frame: Frame) -> None:
        """Stub function for building a frame."""

        chan = Channel("fake", Primitive.BOOLEAN, 1.0)
        while frame.space:
            frame.write(chan)

    return dummy_frame(
        overall_size, "invalid", frame_builder, app_id_basis, bad_crc
    )
