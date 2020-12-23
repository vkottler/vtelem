
"""
vtelem - Class defaults.
"""

# built-in
from typing import Tuple, Any

# internal
from vtelem.enums.primitive import Primitive

ENUM_TYPE = Primitive.UINT8
TIMESTAMP_PRIM = Primitive.UINT64
COUNT_PRIM = Primitive.UINT32
ID_PRIM = Primitive.UINT16

EventType = Tuple[Any, float]
