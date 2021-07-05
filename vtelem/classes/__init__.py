"""
vtelem - Class defaults.
"""

# built-in
from typing import Tuple, Any

# internal
from vtelem.enums.primitive import Primitive

ENUM_TYPE = Primitive.UINT8
TIMESTAMP_PRIM = Primitive.UINT64
METRIC_PRIM = Primitive.UINT32
COUNT_PRIM = METRIC_PRIM
ID_PRIM = Primitive.UINT16

EventType = Tuple[Any, float]

LOG_PERIOD: float = 0.25
