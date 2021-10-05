"""
vtelem - Type definition for use with serializables.
"""

# built-in
from typing import Union, Dict, List

# See RFC 8259.
ObjectKey = Union[int, str]
ObjectElement = Union[float, int, str, bool, None]
ObjectMap = Dict[ObjectKey, ObjectElement]
ObjectData = Dict[
    ObjectKey,
    Union[ObjectElement, List[ObjectElement], ObjectMap],
]
