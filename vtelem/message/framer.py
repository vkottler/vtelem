"""
vtelem - A module exposing message serialization methods.
"""

# built-in
from json import JSONEncoder, dumps
from typing import Dict, Sequence, Tuple, Type

# internal
from vtelem.classes.serdes import ObjectData, Serializable
from vtelem.frame.framer import Framer
from vtelem.frame.message import MessageFrame, frames_required
from vtelem.types.frame import MessageType

# should be a NamedTuple
SerializedFrames = Tuple[Sequence[MessageFrame], int]


class MessageFramer(Framer):
    """A class implementing a message framer for serializing message frames."""

    def __init__(
        self,
        mtu: int,
        app_id_basis: float = None,
        use_crc: bool = True,
    ) -> None:
        """Construct a new message framer."""

        super().__init__(mtu, app_id_basis, use_crc)

        # initialize message numbers
        self.message_numbers: Dict[MessageType, int] = {}
        for message_type in MessageType:
            self.message_numbers[message_type] = 0

    def message_frame(self, time: float = None) -> MessageFrame:
        """Create a new message frame."""

        frame = self.new_frame("message", time)
        assert isinstance(frame, MessageFrame)
        return frame

    def serialize_message(
        self,
        message: bytes,
        time: float = None,
        message_type: MessageType = MessageType.AGNOSTIC,
    ) -> SerializedFrames:
        """Serialize an arbitrary message into one or more frames."""

        frame = self.message_frame(time)
        to_frame = len(message)
        total_frames, per_frame = frames_required(frame, to_frame)

        base_params = MessageFrame.create_fields(
            {
                "message_type": message_type.value,
                "message_number": self.message_numbers[message_type],
                "message_crc": MessageFrame.messag_crc(message),
                "fragment_index": 0,
                "total_fragments": total_frames,
            }
        )
        self.message_numbers[message_type] += 1

        frames = []
        frame_start = 0
        total_bytes = 0
        for idx in range(total_frames):
            assert to_frame
            base_params["fragment_index"].set(idx)
            frame_size = min(to_frame, per_frame)
            frame.initialize(
                base_params, message[frame_start : frame_start + frame_size]
            )
            total_bytes += frame.finalize(self.use_crc)

            frames.append(frame)
            to_frame -= frame_size
            frame_start += frame_size
            if to_frame:
                frame = self.message_frame(time)

        return frames, total_bytes

    def serialize_message_str(
        self,
        message: str,
        time: float = None,
        message_type: MessageType = MessageType.TEXT,
    ) -> SerializedFrames:
        """Serialize an arbitrary String-based message."""

        return self.serialize_message(message.encode(), time, message_type)

    def serialize_message_json(
        self,
        message: ObjectData,
        time: float = None,
        message_type: MessageType = MessageType.JSON,
        cls: Type[JSONEncoder] = None,
        **dump_kwargs,
    ) -> SerializedFrames:
        """Serialize an arbitrary JSON-based message."""

        return self.serialize_message_str(
            dumps(message, cls=cls, **dump_kwargs), time, message_type
        )

    def serialize_object(
        self,
        message: Serializable,
        time: float = None,
        message_type: MessageType = MessageType.JSON,
        **dump_kwargs,
    ) -> SerializedFrames:
        """Serialize an object that supports JSON-serialization."""

        return self.serialize_message_str(
            message.json_str(**dump_kwargs), time, message_type
        )
