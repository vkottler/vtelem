# =====================================
# generator=datazen
# version=1.7.9
# hash=ab69c48c832a19f4915e7cab94613167
# =====================================
"""
vtelem - A definition of the supported frame types for this library.
"""

# built-in
from typing import Dict

# internal
from vtelem.classes.user_enum import UserEnum

FRAME_TYPE_MAP: Dict[int, str] = {
    0: "invalid",
    1: "data",
    2: "event",
}
FRAME_TYPES = UserEnum("frame_type", FRAME_TYPE_MAP)
