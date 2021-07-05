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


class UserEnum:
    """A container for runtime, user-defined enumerations."""

    def __init__(
        self, name: str, values: Dict[int, str], default: str = None
    ) -> None:
        """Build a runtime enumeration."""

        self.enum: Dict[int, str] = defaultdict(lambda: "unknown")
        self.enum.update(values)
        for key, val in self.enum.items():
            self.enum[key] = val.lower()
        self.name = to_snake(name)
        assert len(self.enum.keys()) <= (2 ** (get_size(ENUM_TYPE) * 8))
        assert len(self.enum.keys()) > 0

        # maintain a reverse mapping for convenience
        self.strings: Dict[str, Optional[int]] = defaultdict(lambda: None)
        for key, val in self.enum.items():
            self.strings[val.lower()] = key

        # set a viable default value
        val = default if default is not None else list(self.strings.keys())[0]
        assert val is not None
        self.default_val = val

    def get_str(self, val: int) -> str:
        """Look up the String represented by the integer enum value."""

        return self.enum[val]

    def get_value(self, val: str) -> int:
        """Get the integer value of an enum String."""

        result = self.strings[val.lower()]
        assert result is not None
        return result

    def default(self) -> str:
        """Get the default value for this enum."""

        return self.default_val

    def get_primitive(
        self, value: str, changed_cb: Callable = None
    ) -> TypePrimitive:
        """
        Create a new primitive with an initial value from this enum definition.
        """

        result = TypePrimitive(ENUM_TYPE, changed_cb)
        val = self.strings[value.lower()]
        assert val is not None
        assert result.set(val)
        return result

    def describe(self, indented: bool = False) -> str:
        """Describe this enumeration as a JSON String."""

        indent = 4 if indented else None
        return json.dumps(
            self.enum, indent=indent, sort_keys=True, cls=UserEnumEncoder
        )


class UserEnumEncoder(json.JSONEncoder):
    """A JSON encoder for a primitive enum."""

    def default(self, o) -> dict:
        """Implement serialization for the primitive enum value."""

        assert isinstance(o, UserEnum)
        return {"name": o.name, "mappings": o.enum}


def from_enum(enum_class: Type[Enum]) -> UserEnum:
    """From an enum class, create a user enum."""

    values = {}
    for inst in enum_class:
        assert isinstance(inst.value, int)
        assert inst.value not in values
        values[inst.value] = inst.name.lower()
    return UserEnum(class_to_snake(enum_class), values)
