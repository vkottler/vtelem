# =====================================
# generator=datazen
# version=2.1.1
# hash=e82122bb683e32a9f7a7add208f34950
# =====================================
"""
vtelem - Useful type definitions for working with frames.
"""

# built-in
from enum import IntEnum
from typing import NamedTuple, Optional

# internal
from vtelem.classes.user_enum import from_enum
from vtelem.enums.primitive import Primitive


class FrameType(IntEnum):
    """An enumeration for possible frame types."""

    DATA = 1
    EVENT = 2
    INVALID = 0
    MESSAGE = 3
    STREAM = 4


class FrameHeader(NamedTuple):
    """Elements contained in a frame header."""

    length: int
    app_id: int
    type: FrameType
    timestamp: int
    size: int


class FrameFooter(NamedTuple):
    """Elements contained in a frame footer."""

    crc: Optional[int]


class ParsedFrame(NamedTuple):
    """A type defining fields in a parsed frame."""

    header: FrameHeader
    body: dict
    footer: FrameFooter


class FieldType(NamedTuple):
    """A pairing of a field name and its type."""

    name: str
    type: Primitive


class MessageType(IntEnum):
    """An enumeration for possible frame types."""

    AGNOSTIC = 0
    TEXT = 1
    JSON = 2
    ENUM = 3
    ENUM_REGISTRY = 4
    PRIMITIVE = 5


MESSAGE_TYPES = from_enum(MessageType)
