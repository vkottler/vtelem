"""
vtelem - Implements an object for storing a runtime enumeration.
"""

# built-in
from collections import defaultdict
from enum import IntEnum
from typing import cast, Dict, Callable, Iterator, Optional, Type

# internal
from vtelem.classes import DEFAULTS
from vtelem.classes.serdes import ObjectData, ObjectMap
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.enums.primitive import get_size
from vtelem.names import to_snake, class_to_snake


class UserEnum:
    """A container for runtime, user-defined enumerations."""

    def __init__(
        self, name: str, values: Dict[int, str], default: str = None
    ) -> None:
        """Build a runtime enumeration."""

        self.data: ObjectData = {}
        self.data["name"] = to_snake(name)

        self.enum: Dict[int, str] = defaultdict(lambda: "unknown")
        self.enum.update(values)
        for key, val in self.enum.items():
            self.enum[key] = val.lower()

        assert len(self.enum.keys()) <= (2 ** (get_size(DEFAULTS["enum"]) * 8))
        assert len(self.enum.keys()) > 0
        mappings: ObjectMap = {}
        mappings.update(cast(ObjectMap, self.enum))
        self.data["mappings"] = mappings

        # maintain a reverse mapping for convenience
        self.strings: Dict[str, Optional[int]] = defaultdict(lambda: None)
        for key, val in self.enum.items():
            self.strings[val.lower()] = key

        # set a viable default value
        val = default if default is not None else list(self.strings.keys())[0]
        assert val is not None
        self.data["default"] = val

    @property
    def default(self) -> str:
        """Get the default value for this enum."""

        return cast(str, self.data["default"])

    @property
    def name(self) -> str:
        """Get the name of this enum."""

        return cast(str, self.data["name"])

    def __iter__(self) -> Iterator[str]:
        """Iterate over all valid String keys in this enum."""

        options = [x for x in self.strings if x is not None]
        return iter(options)

    def get_str(self, val: int) -> str:
        """Look up the String represented by the integer enum value."""

        return self.enum[val]

    def get_value(self, val: str) -> int:
        """Get the integer value of an enum String."""

        result = self.strings[val.lower()]
        assert result is not None
        return result

    def get_primitive(
        self, value: str, changed_cb: Callable = None
    ) -> TypePrimitive:
        """
        Create a new primitive with an initial value from this enum definition.
        """

        result = new_default("enum", changed_cb)
        val = self.strings[value.lower()]
        assert val is not None
        assert result.set(val)
        return result


def from_enum(enum_class: Type[IntEnum]) -> UserEnum:
    """From an enum class, create a user enum."""

    values = {}
    for inst in enum_class:
        assert isinstance(inst.value, int)
        assert inst.value not in values
        values[inst.value] = inst.name.lower()
    return UserEnum(class_to_snake(enum_class), values)
