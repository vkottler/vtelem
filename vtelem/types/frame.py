# =====================================
# generator=datazen
# version=1.7.9
# hash=132b6c30deef9606da5463c457ebe601
# =====================================
"""
vtelem - Useful type definitions for working with frames.
"""

# built-in
from enum import IntEnum
from typing import NamedTuple, Optional


class FrameType(IntEnum):
    """An enumeration for possible frame types."""

    INVALID = 0
    DATA = 1
    EVENT = 2
    MESSAGE = 3
    STREAM = 4


class FrameHeader(NamedTuple):
    """Elements contained in a frame header."""

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
