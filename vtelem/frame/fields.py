"""
vtelem - Data structures for organizing frame-field information.
"""

# built-in
from typing import List

# internal
from vtelem.classes import DEFAULTS
from vtelem.frame import FieldType


MESSAGE_FIELDS: List[FieldType] = [
    FieldType("message_type", DEFAULTS["enum"]),
    FieldType("message_number", DEFAULTS["id"]),
    FieldType("message_crc", DEFAULTS["crc"]),
    FieldType("fragment_index", DEFAULTS["id"]),
    FieldType("total_fragments", DEFAULTS["id"]),
]
