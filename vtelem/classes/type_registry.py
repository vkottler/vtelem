"""
vtelem - Contains a class for managing known type primitives.
"""

# built-in
from typing import Tuple, Optional, List

# internal
from vtelem.enums.primitive import Primitive, PrimitiveEncoder, get_name
from .registry import Registry


class TypeRegistry(Registry[Primitive]):
    """
    A class for managing types that can be registered and referenced by a
    name and an integer identifier.
    """

    def __init__(
        self, initial_types: List[Tuple[str, Primitive]] = None
    ) -> None:
        """Construct a new type registry, optionally add initial types."""

        super().__init__("types", initial_types)

    def get_type(self, type_id: int) -> Optional[Primitive]:
        """Obtain a type's data by its integer identifier."""

        return self.get_item(type_id)

    def describe(self, indented: bool = False) -> str:
        """Obtain a JSON String of the type registry's current state."""

        return self.describe_raw(indented, PrimitiveEncoder)


def get_default() -> TypeRegistry:
    """
    Get the default type registry, with the known primitive types
    pre-registered.
    """

    return TypeRegistry([(get_name(prim), prim) for prim in Primitive])
