# =====================================
# generator=datazen
# version=1.7.9
# hash=acef66ef1475a692f5480ee69acac871
# =====================================
"""
vtelem - A definition of the supported frame types for this library.
"""

# built-in
from typing import Callable, Dict

# internal
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.channel_registry import ChannelRegistry
from vtelem.classes.user_enum import UserEnum
from vtelem.parsing.frames import (
    parse_invalid_frame,
    parse_data_frame,
    parse_event_frame,
    parse_message_frame,
    parse_stream_frame,
)

FrameParser = Callable[[dict, ByteBuffer, ChannelRegistry], None]
PARSERS: Dict[str, FrameParser] = {
    "invalid": parse_invalid_frame,
    "data": parse_data_frame,
    "event": parse_event_frame,
    "message": parse_message_frame,
    "stream": parse_stream_frame,
}

FRAME_TYPE_MAP: Dict[int, str] = {
    0: "invalid",
    1: "data",
    2: "event",
    3: "message",
    4: "stream",
}
FRAME_TYPES = UserEnum("frame_type", FRAME_TYPE_MAP)

MESSAGE_TYPE_MAP: Dict[int, str] = {
    0: "agnostic",
    1: "text",
    2: "json",
}
MESSAGE_TYPES = UserEnum("message_type", MESSAGE_TYPE_MAP)
