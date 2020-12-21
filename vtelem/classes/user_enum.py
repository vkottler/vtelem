
"""
vtelem - Implements an object for storing a runtime enumeration.
"""

# built-in
from collections import defaultdict
import json
from typing import Dict

# internal
from vtelem.enums.primitive import get_size
from . import ENUM_TYPE


class UserEnum(dict):
    """ A container for runtime, user-defined enumerations. """

    def __init__(self, name: str, values: Dict[int, str]) -> None:
        """ Build a runtime enumeration. """

        super().__init__()
        self.enum: Dict[int, str] = defaultdict(lambda: "UNKNOWN")
        self.enum.update(values)
        self.name = name
        assert len(self.enum) <= (2 ** (get_size(ENUM_TYPE) * 8))

    def get_str(self, val: int) -> str:
        """ Look up the String represented by the integer enum value. """

        return self.enum[val]

    def describe(self, indented: bool = False) -> str:
        """ Describe this enumeration as a JSON String. """

        indent = 4 if indented else None
        return json.dumps(self.enum, indent=indent, sort_keys=True)
