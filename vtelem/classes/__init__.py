# =====================================
# generator=datazen
# version=2.1.1
# hash=8037b097b2a931af74e265e2bba7f402
# =====================================
"""
vtelem - Class defaults.
"""

# built-in
from typing import Any, Dict, Tuple

# internal
from vtelem.enums.primitive import Primitive

DEFAULTS: Dict[str, Primitive] = {
    "version": Primitive.UINT8,
    "enum": Primitive.UINT8,
    "timestamp": Primitive.UINT64,
    "metric": Primitive.UINT32,
    "count": Primitive.UINT32,
    "crc": Primitive.UINT32,
    "id": Primitive.UINT16,
}

EventType = Tuple[Any, float]

LOG_PERIOD: float = 0.25
