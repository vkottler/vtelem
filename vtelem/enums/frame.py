# =====================================
# generator=datazen
# version=1.7.11
# hash=0c18bf173ef7489425f320bdb0f2de3e
# =====================================
"""
vtelem - A definition of the supported frame types for this library.
"""

# built-in
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


FrameParser = Callable[[FrameHeader, ByteBuffer, ChannelRegistry], dict]
PARSERS: Dict[FrameType, FrameParser] = {
    FrameType.INVALID: parse_invalid_frame,
    FrameType.DATA: parse_data_frame,
    FrameType.EVENT: parse_event_frame,
    FrameType.MESSAGE: parse_message_frame,
    FrameType.STREAM: parse_stream_frame,
}
FRAME_TYPES = from_enum(FrameType)
