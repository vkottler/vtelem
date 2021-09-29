"""
vtelem - Common test resources.
"""

# built-in
from enum import Enum

# module under test
from vtelem.classes.serdes import ObjectData, Serializable, SerializableParams

KEYS = "abc"


class EnumA(Enum):
    """Sample enumeration."""

    A = 0
    B = 1
    C = 2


def default_object(
    data: ObjectData = None,
    params: SerializableParams = None,
) -> Serializable:
    """Get a generic serializable object."""

    if data is None:
        data = {}
        for idx, string in enumerate(KEYS):
            data[string] = idx + 1
    return Serializable(data, params)
