# =====================================
# generator=datazen
# version=1.7.9
# hash=d2192197ca211c3b77e43f85bdc41ee7
# =====================================
"""
vtelem - A definition of the supported frame types for this library.
"""

# built-in
from enum import IntEnum
from typing import Callable, Dict

# internal
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.user_enum import from_enum
from vtelem.parsing.frames import (
    parse_invalid_frame,
    parse_data_frame,
    parse_event_frame,
    parse_message_frame,
    parse_stream_frame,
)
from vtelem.types.frame import FrameType, FrameHeader


class MessageType(IntEnum):
    """An enumeration for possible frame types."""

    AGNOSTIC = 0
    TEXT = 1
    JSON = 2


FrameParser = Callable[[FrameHeader, ByteBuffer, ChannelRegistry], dict]
PARSERS: Dict[FrameType, FrameParser] = {
    FrameType.INVALID: parse_invalid_frame,
    FrameType.DATA: parse_data_frame,
    FrameType.EVENT: parse_event_frame,
    FrameType.MESSAGE: parse_message_frame,
    FrameType.STREAM: parse_stream_frame,
}
FRAME_TYPES = from_enum(FrameType)
MESSAGE_TYPES = from_enum(MessageType)
