# =====================================
# generator=datazen
# version=2.1.1
# hash=626c46af383ec2f55f44539038229131
# =====================================
"""
vtelem - A definition of the supported frame types for this library.
"""

# built-in
from typing import Callable, Dict

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.user_enum import from_enum
from vtelem.parsing.frames import (
    parse_data_frame,
    parse_event_frame,
    parse_invalid_frame,
    parse_message_frame,
    parse_stream_frame,
)
from vtelem.types.frame import FrameHeader, FrameType

FrameParser = Callable[[FrameHeader, ByteBuffer, ChannelRegistry], dict]
PARSERS: Dict[FrameType, FrameParser] = {
    FrameType.DATA: parse_data_frame,
    FrameType.EVENT: parse_event_frame,
    FrameType.INVALID: parse_invalid_frame,
    FrameType.MESSAGE: parse_message_frame,
    FrameType.STREAM: parse_stream_frame,
}
FRAME_TYPES = from_enum(FrameType)
