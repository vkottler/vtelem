# =====================================
# generator=datazen
# version=1.7.9
# hash=bd9a431625b4df30b83cf32e0fa25023
# =====================================
"""
vtelem - A definition of the supported primitive types for this library.
"""

# built-in
from enum import Enum
from json import JSONEncoder
import random
from typing import Any, Callable, NamedTuple, Tuple, Type


class BasePrimitive(NamedTuple):
    """A schema for primitive enum values."""

    fmt: str
    type: Type
    size: int
    name: str
    signed: bool
    min: int = 0
    max: int = 0
    validate: Callable[[Any, int], bool] = lambda _, __: True


def integer_bounds(byte_count: int, signed: bool) -> Tuple[int, int]:
    """Compute maximum and minimum values given size and signedness."""

    min_val = 0 if not signed else -1 * (2 ** (byte_count * 8 - 1))
    width = 8 * byte_count if not signed else 8 * byte_count - 1
    return min_val, (2 ** width) - 1


def integer_can_hold(prim: BasePrimitive, val: int) -> bool:
    """
    Simple checl to see if a primitive can hold this arbitrary integer value.
    """

    return prim.min <= val <= prim.max


class Primitive(Enum):
    """
    An enumeration containing the supported primitive types and their 'struct'
    format specifier.
    """

    BOOLEAN = BasePrimitive("?", bool, 1, "boolean", False)
    INT8 = BasePrimitive(
        "b",
        int,
        1,
        "int8",
        True,
        *integer_bounds(1, True),
        integer_can_hold,
    )
    UINT8 = BasePrimitive(
        "B",
        int,
        1,
        "uint8",
        False,
        *integer_bounds(1, False),
        integer_can_hold,
    )
    INT16 = BasePrimitive(
        "h",
        int,
        2,
        "int16",
        True,
        *integer_bounds(2, True),
        integer_can_hold,
    )
    UINT16 = BasePrimitive(
        "H",
        int,
        2,
        "uint16",
        False,
        *integer_bounds(2, False),
        integer_can_hold,
    )
    INT32 = BasePrimitive(
        "i",
        int,
        4,
        "int32",
        True,
        *integer_bounds(4, True),
        integer_can_hold,
    )
    UINT32 = BasePrimitive(
        "I",
        int,
        4,
        "uint32",
        False,
        *integer_bounds(4, False),
        integer_can_hold,
    )
    INT64 = BasePrimitive(
        "q",
        int,
        8,
        "int64",
        True,
        *integer_bounds(8, True),
        integer_can_hold,
    )
    UINT64 = BasePrimitive(
        "Q",
        int,
        8,
        "uint64",
        False,
        *integer_bounds(8, False),
        integer_can_hold,
    )
    FLOAT = BasePrimitive("f", float, 4, "float", True)
    DOUBLE = BasePrimitive("d", float, 8, "double", True)


def random_integer(prim: Primitive) -> int:
    """
    Get a random integer that's guaranteed to fit in the provided primitive.
    """

    assert prim != Primitive.BOOLEAN
    assert prim != Primitive.FLOAT
    assert prim != Primitive.DOUBLE
    return random.randint(prim.value.min, prim.value.max)


class PrimitiveEncoder(JSONEncoder):
    """A JSON encoder for a primitive enum."""

    def default(self, o) -> dict:
        """Implement serialization for the primitive enum value."""

        assert isinstance(o, Primitive)
        val: BasePrimitive = o.value
        data = {
            "size": val.size,
            "name": val.name,
            "signed": val.signed,
        }
        if val.min != 0 or val.max != 0:
            data["min"] = val.min
            data["max"] = val.max
        return data


def get_name(inst: Primitive) -> str:
    """Get a primitive's canonical name."""

    return inst.value.name


def get_fstring(inst: Primitive) -> str:
    """Get the 'struct' format specifier for a primitive."""

    return inst.value.fmt


def get_size(inst: Primitive) -> int:
    """Get the size of a primitive."""

    return inst.value.size


def default_val(inst: Primitive) -> Any:
    """Get the default value for a specific primitive."""

    return inst.value.type()


INTEGER_PRIMITIVES = [
    Primitive.INT8,
    Primitive.UINT8,
    Primitive.INT16,
    Primitive.UINT16,
    Primitive.INT32,
    Primitive.UINT32,
    Primitive.INT64,
    Primitive.UINT64,
]
