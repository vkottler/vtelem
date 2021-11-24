"""
vtelem - Data structures for organizing frame-field information.
"""

# built-in
from typing import List, NamedTuple

# internal
from vtelem.classes import DEFAULTS
from vtelem.types.frame import FieldType, MessageType

MESSAGE_FIELDS: List[FieldType] = [
    FieldType("message_type", DEFAULTS["enum"]),
    FieldType("message_number", DEFAULTS["id"]),
    FieldType("message_crc", DEFAULTS["crc"]),
    FieldType("fragment_index", DEFAULTS["id"]),
    FieldType("total_fragments", DEFAULTS["id"]),
]


class ParsedMessage(NamedTuple):
    """An encapsulation of fields present in a parsed message."""

    type: MessageType
    number: int
    crc: int
    fragment_index: int
    total_fragments: int
    data: bytes


def to_parsed(data: dict) -> ParsedMessage:
    """From raw parsed data, construct a named tuple."""

    for field in MESSAGE_FIELDS:
        assert field.name in data

    return ParsedMessage(
        MessageType(data["message_type"]),
        data["message_number"],
        data["message_crc"],
        data["fragment_index"],
        data["total_fragments"],
        data["fragment_bytes"],
    )
