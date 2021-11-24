"""
vtelem - Common type definitions for the command-queue daemon.
"""

# built-in
from typing import Callable, Dict, List, Optional, Tuple

ConsumerType = Callable[[dict], Tuple[bool, str]]
ResultCbType = Callable[[bool, str], None]
HandlersType = Dict[
    str, List[Tuple[ConsumerType, Optional[ResultCbType], str]]
]
