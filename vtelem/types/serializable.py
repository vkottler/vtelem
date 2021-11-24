"""
vtelem - Type definition for use with serializables.
"""

# built-in
from typing import Dict, List, Union

# See RFC 8259.
ObjectKey = Union[int, str]
ObjectElement = Union[float, int, str, bool, None]
ObjectMap = Dict[ObjectKey, ObjectElement]
ObjectData = Dict[
    ObjectKey,
    Union[ObjectElement, List[ObjectElement], ObjectMap],
]
