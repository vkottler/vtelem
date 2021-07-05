"""
vtelem - Test the correctness of primitive information.
"""

# module under test
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.enums.primitive import (
    Primitive,
    get_integer_max,
    get_integer_min,
    integer_can_hold,
    random_integer,
    INTEGER_PRIMITIVES,
)


def test_primitive_max_min():
    """Test that our internal representation of integers is correct."""

    # 8-bit
    assert get_integer_max(Primitive.UINT8) == 255
    assert get_integer_min(Primitive.UINT8) == 0
    assert get_integer_max(Primitive.INT8) == 127
    assert get_integer_min(Primitive.INT8) == -128

    # 16-bit
    assert get_integer_max(Primitive.UINT16) == 65535
    assert get_integer_min(Primitive.UINT16) == 0
    assert get_integer_max(Primitive.INT16) == 32767
    assert get_integer_min(Primitive.INT16) == -32768

    # 32-bit
    assert get_integer_max(Primitive.UINT32) == 4294967295
    assert get_integer_min(Primitive.UINT32) == 0
    assert get_integer_max(Primitive.INT32) == 2147483647
    assert get_integer_min(Primitive.INT32) == -2147483648

    # 64-bit
    assert get_integer_max(Primitive.UINT64) == 18446744073709551615
    assert get_integer_min(Primitive.UINT64) == 0
    assert get_integer_max(Primitive.INT64) == 9223372036854775807
    assert get_integer_min(Primitive.INT64) == -9223372036854775808

    assert integer_can_hold(Primitive.UINT8, 0)
    assert integer_can_hold(Primitive.UINT8, 255)

    # test random-integer generation
    for _ in range(1000):
        for prim in INTEGER_PRIMITIVES:
            assert integer_can_hold(prim, random_integer(prim))

    # test validators
    unsigned_prim = TypePrimitive(Primitive.UINT8)
    signed_prim = TypePrimitive(Primitive.INT8)
    assert str(unsigned_prim) is not None
    assert str(signed_prim) is not None
    assert not unsigned_prim.set(256)
    assert not unsigned_prim.set(-1)
    assert not signed_prim.set(128)
    assert not signed_prim.set(-129)
    assert unsigned_prim.set(5)
    assert signed_prim.set(5)
    assert unsigned_prim != signed_prim
    assert signed_prim.set(6)
    assert unsigned_prim != signed_prim
    new_unsigned_prim = TypePrimitive(Primitive.UINT8)
    assert new_unsigned_prim.set(5)
    assert unsigned_prim == new_unsigned_prim
