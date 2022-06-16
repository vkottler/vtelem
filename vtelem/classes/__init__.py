# =====================================
# generator=datazen
# version=3.0.7
# hash=5d53990330fd2c38af37be5803465692
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
