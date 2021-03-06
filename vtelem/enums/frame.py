# =====================================
# generator=datazen
# version=1.7.9
# hash=b31b1d5b38fcfacd0b9e99f2a016918a
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
from vtelem.parsing import (
    parse_invalid_frame,
    parse_data_frame,
    parse_event_frame,
)

FrameParser = Callable[[dict, ByteBuffer, ChannelRegistry], None]
PARSERS: Dict[str, FrameParser] = {
    "invalid": parse_invalid_frame,
    "data": parse_data_frame,
    "event": parse_event_frame,
}

FRAME_TYPE_MAP: Dict[int, str] = {
    0: "invalid",
    1: "data",
    2: "event",
}
FRAME_TYPES = UserEnum("frame_type", FRAME_TYPE_MAP)
