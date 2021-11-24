"""
vtelem - Convert the primitive enumeration to a serializable object.
"""

# built-in
from typing import FrozenSet

# internal
from vtelem.classes.serdes import Serializable
from vtelem.enums.primitive import Primitive, get_name, to_dict
from vtelem.types.serializable import ObjectData


class SerializablePrimitive(Serializable):
    """
    A class for bootstrapping the existing primitive assets to be serializable.
    """

    def init(self, data: ObjectData) -> None:
        """Obtain a reference to the real primitive instance."""

        prim = None
        for candidate in Primitive:
            if get_name(candidate) == data["name"]:
                prim = candidate
        assert prim is not None
        self.primitive: Primitive = prim


def from_primitive(prim: Primitive, **kwargs) -> SerializablePrimitive:
    """Convert a primitive into a serializable form."""

    return SerializablePrimitive(to_dict(prim), **kwargs)


def get_all(**kwargs) -> FrozenSet[SerializablePrimitive]:
    """Get all serializable primitives as a set."""

    return frozenset(from_primitive(x, **kwargs) for x in Primitive)
