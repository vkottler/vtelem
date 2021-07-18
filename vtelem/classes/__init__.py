# =====================================
# generator=datazen
# version=1.7.8
# hash=93606f47f8ebcedde98631ef9d81bfd2
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
    "id": Primitive.UINT16,
}

EventType = Tuple[Any, float]

LOG_PERIOD: float = 0.25
