"""
vtelem - A definition of the supported primitive types for this library.
"""

# built-in
from copy import copy
from enum import Enum
from json import JSONEncoder
import random
from typing import Any


def build_primitive(
    fmt: str, inst: type, size: int, name: str, signed: bool
) -> dict:
    """Build a primitive dictionary from data."""

    return {
        "format": fmt,
        "type": inst,
        "size": size,
        "name": name,
        "signed": signed,
        "validate": lambda _, __: True,
    }


class Primitive(Enum):
    """
    An enumeration containing the supported primitive types and their 'struct'
    format specifier.
    """

    BOOL = build_primitive("?", bool, 1, "boolean", False)
    INT8 = build_primitive("b", int, 1, "int8", True)
    UINT8 = build_primitive("B", int, 1, "uint8", False)
    INT16 = build_primitive("h", int, 2, "int16", True)
    UINT16 = build_primitive("H", int, 2, "uint16", False)
    INT32 = build_primitive("i", int, 4, "int32", True)
    UINT32 = build_primitive("I", int, 4, "uint32", False)
    INT64 = build_primitive("q", int, 8, "int64", True)
    UINT64 = build_primitive("Q", int, 8, "uint64", False)
    FLOAT = build_primitive("f", float, 4, "float", True)
    DOUBLE = build_primitive("d", float, 8, "double", True)


def random_integer(prim: Primitive) -> int:
    """
    Get a random integer that's guaranteed to fit in the provided primitive.
    """

    assert prim != Primitive.BOOL
    assert prim != Primitive.FLOAT
    assert prim != Primitive.DOUBLE
    return random.randint(get_integer_min(prim), get_integer_max(prim))


def integer_can_hold(prim: Primitive, val: int) -> bool:
    """
    Simple checl to see if a primitive can hold this arbitrary integer value.
    """

    return prim.value["min"] <= val <= prim.value["max"]


def get_integer_max(prim: Primitive) -> int:
    """Get the maximum value for an integer type."""

    assert prim != Primitive.BOOL
    assert prim != Primitive.FLOAT
    assert prim != Primitive.DOUBLE

    width = prim.value["size"] * 8
    if prim.value["signed"]:
        width -= 1

    return (2 ** width) - 1


def get_integer_min(prim: Primitive) -> int:
    """Get the minimum value for an integer type."""

    assert prim != Primitive.BOOL
    assert prim != Primitive.FLOAT
    assert prim != Primitive.DOUBLE

    if not prim.value["signed"]:
        return 0
    return -1 * (2 ** (prim.value["size"] * 8 - 1))


class PrimitiveEncoder(JSONEncoder):
    """A JSON encoder for a primitive enum."""

    def default(self, o) -> dict:
        """Implement serialization for the primitive enum value."""

        assert isinstance(o, Primitive)
        result = copy(o.value)
        del result["validate"]
        result["type"] = str(result["type"])
        return result


def get_name(inst: Primitive) -> str:
    """Get a primitive's canonical name."""

    return inst.value["name"]


def get_fstring(inst: Primitive) -> str:
    """Get the 'struct' format specifier for a primitive."""

    return inst.value["format"]


def get_size(inst: Primitive) -> int:
    """Get the size of a primitive."""

    return inst.value["size"]


def default_val(inst: Primitive) -> Any:
    """Get the default value for a specific primitive."""

    return inst.value["type"]()


INTEGER_PRIMITIVES = [
    Primitive.UINT8,
    Primitive.INT8,
    Primitive.UINT16,
    Primitive.INT16,
    Primitive.UINT32,
    Primitive.INT32,
    Primitive.UINT64,
    Primitive.INT64,
]

for _prim in INTEGER_PRIMITIVES:
    _prim.value["max"] = get_integer_max(_prim)
    _prim.value["min"] = get_integer_min(_prim)
    _prim.value["validate"] = integer_can_hold
