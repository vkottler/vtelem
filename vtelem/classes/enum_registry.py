
"""
vtelem - Contains a class for managing known enumeration sets.
"""

# built-in
from collections import defaultdict
import logging
from typing import Tuple, List

# internal
from . import ENUM_TYPE
from .registry import Registry
from .type_registry import TypeRegistry
from .user_enum import UserEnum

LOG = logging.getLogger(__name__)


class EnumRegistry(Registry[UserEnum]):
    """ A class for storing runtime enumeration registrations. """

    def __init__(self, initial_enums: List[UserEnum] = None) -> None:
        """ Construct a new enum registry. """

        super().__init__("enums", None)
        self.data["global_mappings"] = defaultdict(lambda: -1)
        if initial_enums is not None:
            for enum in initial_enums:
                self.add_enum(enum)

    def add_enum(self, enum: UserEnum) -> Tuple[bool, int]:
        """ Attempt to register an enumeration. """

        return self.add(enum.name, enum)

    def describe(self, indented: bool = False) -> str:
        """ Obtain a JSON String of the enum registry's current state. """

        return self.describe_raw(indented)

    def export(self, registry: TypeRegistry) -> bool:
        """
        Export registered enumerations to a type registry and keep track of
        this mapping.
        """

        with self.lock:
            for enum_id, enum_data in self.data["enums"].items():

                # determine if this enum has already been registered
                curr_id = registry.get_id(enum_data.name)
                if curr_id is not None:
                    expected_id = self.data["global_mappings"][curr_id]
                    if expected_id != enum_id:
                        log_str = ("couldn't register '%s', type has value " +
                                   "%d (expected %d)")
                        LOG.error(log_str, enum_data.name, enum_id,
                                  expected_id)
                        return False
                    LOG.debug("enum '%s' already registered as %d",
                              enum_data.name, expected_id)
                    continue

                # remember the mapping for this enum to the global type
                # registry
                result = registry.add(enum_data.name, ENUM_TYPE)
                assert result[0]
                self.data["global_mappings"][result[1]] = enum_id

        return True
