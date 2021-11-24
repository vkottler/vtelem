"""
vtelem - A module providing assets for managing enumerations at runtime.
"""

# built-in
from enum import IntEnum
from typing import Dict, Type, cast

# internal
from vtelem.classes.serdes import ObjectData, ObjectMap, Serializable, max_key
from vtelem.classes.time_entity import LockEntity
from vtelem.classes.user_enum import UserEnum, from_enum


class EnumRegistry(Serializable, LockEntity):
    """
    A class for managing runtime enumerations, so that enumerations can be
    referenced by integer values.
    """

    def init(self, data: ObjectData) -> None:
        """Initialize this enum registry from object data."""

        with self.lock:
            # Ensure that 'mappings' has integer keys.
            self.coerce_int_keys(["mappings"], data)

            # Set 'curr_id' so that the next enum added has the correct id.
            mappings: ObjectMap = cast(ObjectMap, data["mappings"])
            self.curr_id: int = max_key(mappings) + 1

            # Load real enum objects from the data.
            self.enums: Dict[str, UserEnum] = {}
            if self.enum_data:
                for name in mappings.values():
                    assert isinstance(name, str)
                    self.enums[name] = UserEnum(
                        self.enum_data[name], manager=self.manager
                    )

    @property
    def enum_data(self) -> Dict[str, ObjectData]:
        """Get the mapping of enum name to underlying enum data."""

        if "enums" not in self.data:
            self.data["enums"] = {}
        enums = cast(Dict[str, ObjectData], self.data["enums"])
        return enums

    def get_enum(self, enum_id: int) -> UserEnum:
        """Get a user enum by its integer identifier."""

        mappings: ObjectMap = cast(ObjectMap, self.data["mappings"])
        name = mappings[enum_id]
        assert isinstance(name, str)
        return self.enums[name]

    def add(self, enum: UserEnum) -> int:
        """Add an enum to the registry."""

        assert enum.name not in self.data
        with self.lock:
            # Store a reference to the serializable data directly.
            self.enum_data[enum.name] = enum.data

            # Store a reference to the real enum object.
            self.enums[enum.name] = enum

            # Store an integer-to-name mapping for each named enum
            # (similar to an enum itself).
            this_id = self.curr_id
            mappings: ObjectMap = cast(ObjectMap, self.data["mappings"])
            mappings[this_id] = enum.name
            self.curr_id += 1
            return this_id

    def add_from_enum(self, enum_cls: Type[IntEnum]) -> int:
        """Register an enum from an enum class."""

        return self.add(from_enum(enum_cls))
