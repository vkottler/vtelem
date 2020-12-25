
"""
vtelem - Implements an object for storing a runtime enumeration.
"""

# built-in
from collections import defaultdict
from enum import Enum
import json
from typing import Dict, Callable, Optional, Type

# internal
from vtelem.enums.primitive import get_size
from vtelem.names import to_snake, class_to_snake
from . import ENUM_TYPE
from .type_primitive import TypePrimitive


class UserEnum(dict):
    """ A container for runtime, user-defined enumerations. """

    def __init__(self, name: str, values: Dict[int, str]) -> None:
        """ Build a runtime enumeration. """

        super().__init__()
        self.enum: Dict[int, str] = defaultdict(lambda: "UNKNOWN")
        self.enum.update(values)
        self.name = to_snake(name)
        assert len(self.enum) <= (2 ** (get_size(ENUM_TYPE) * 8))

        # maintain a reverse mapping for convenience
        self.strings: Dict[str, Optional[int]] = defaultdict(lambda: None)
        for key, val in self.enum.items():
            self.strings[val] = key

    def get_str(self, val: int) -> str:
        """ Look up the String represented by the integer enum value. """

        return self.enum[val]

    def get_value(self, val: str) -> int:
        """ Get the integer value of an enum String. """

        result = self.strings[val]
        assert result is not None
        return result

    def get_primitive(self, value: str,
                      changed_cb: Callable = None) -> TypePrimitive:
        """
        Create a new primitive with an initial value from this enum definition.
        """

        result = TypePrimitive(ENUM_TYPE, changed_cb)
        val = self.strings[value]
        assert val is not None
        assert result.set(val)
        return result

    def describe(self, indented: bool = False) -> str:
        """ Describe this enumeration as a JSON String. """

        indent = 4 if indented else None
        return json.dumps(self.enum, indent=indent, sort_keys=True)


def from_enum(enum_class: Type[Enum]) -> UserEnum:
    """ From an enum class, create a user enum. """

    values = {}
    for inst in enum_class:
        assert isinstance(inst.value, int)
        assert inst.value not in values
        values[inst.value] = inst.name.lower()
    return UserEnum(class_to_snake(enum_class), values)
