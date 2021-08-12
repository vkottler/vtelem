"""
vtelem - A module exposing message serialization methods.
"""

# built-in
from typing import Dict, Tuple, Sequence

# internal
from vtelem.enums.frame import MessageType
from vtelem.frame.framer import Framer
from vtelem.frame.message import MessageFrame, frames_required


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
    ) -> Tuple[Sequence[MessageFrame], int]:
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
    ) -> Tuple[Sequence[MessageFrame], int]:
        """Serialize an arbitrary String-based message."""

        return self.serialize_message(message.encode(), time, message_type)
