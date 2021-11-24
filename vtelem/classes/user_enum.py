"""
vtelem - Implements an object for storing a runtime enumeration.
"""

# built-in
from collections import defaultdict
from enum import IntEnum
from typing import Callable, Dict, Iterator, Optional, Type, cast

# internal
from vtelem.classes import DEFAULTS
from vtelem.classes.serdes import (
    ObjectData,
    ObjectMap,
    Serializable,
    SerializableParams,
)
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.enums.primitive import get_size
from vtelem.names import class_to_snake, to_snake
from vtelem.schema.manager import SchemaManager

IntStrMap = Dict[int, str]


def coerce_enum(values: IntStrMap) -> IntStrMap:
    """
    Given a map of integers to Strings, ensure that a returned map conforms
    strictly to runtime enumeration conventions.
    """

    enum: Dict[int, str] = defaultdict(lambda: "unknown")
    enum.update(values)
    for key, val in enum.items():
        enum[key] = val.lower()

    # Ensure this data is valid in the context of a protocol "enum" store.
    assert len(enum.keys()) <= (2 ** (get_size(DEFAULTS["enum"]) * 8))
    assert len(enum.keys()) > 0

    return enum


def reverse_map(enum_map: IntStrMap) -> Dict[str, Optional[int]]:
    """
    Create a reverse mapping of an int->str map that returns None by default.
    """

    strings: Dict[str, Optional[int]] = defaultdict(lambda: None)
    for key, val in enum_map.items():
        strings[val.lower()] = key
    return strings


def user_enum_data(
    name: str, values: IntStrMap, default: str = None
) -> ObjectData:
    """Create object data for a runtime enumeration from constituents."""

    return {
        "name": to_snake(name),
        "mappings": cast(ObjectMap, coerce_enum(values)),
        "default": default,
    }


class UserEnum(Serializable):
    """A container for runtime, user-defined enumerations."""

    def init(self, data: ObjectData) -> None:
        """
        Can be implemented to set up a serializable from some initial data.
        """

        # Maintain a reverse mapping for convenience.
        self.coerce_int_keys(["mappings"], data)
        self.strings = reverse_map(cast(IntStrMap, data["mappings"]))

        # Set a viable default value.
        default = data["default"]
        val = default if default is not None else list(self.strings.keys())[0]
        assert val is not None
        data["default"] = val

    @property
    def default(self) -> str:
        """Get the default value for this enum."""

        return cast(str, self.data["default"])

    def __iter__(self) -> Iterator[str]:
        """Iterate over all valid String keys in this enum."""

        options = [x for x in self.strings if x is not None]
        return iter(options)

    def get_str(self, val: int) -> str:
        """Look up the String represented by the integer enum value."""

        mappings = cast(ObjectMap, self.data["mappings"])
        return cast(str, mappings[val])

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


def user_enum(
    name: str,
    values: IntStrMap,
    default: str = None,
    manager: SchemaManager = None,
) -> UserEnum:
    """Create a user enum from a name and map of values."""

    params = None
    if manager is not None:
        params = SerializableParams(schema=UserEnum.schema(manager))
    return UserEnum(user_enum_data(name, values, default), params)


def from_enum(enum_class: Type[IntEnum]) -> UserEnum:
    """From an enum class, create a user enum."""

    values = {}
    for inst in enum_class:
        assert isinstance(inst.value, int)
        assert inst.value not in values
        values[inst.value] = inst.name.lower()
    return user_enum(class_to_snake(enum_class), values)
