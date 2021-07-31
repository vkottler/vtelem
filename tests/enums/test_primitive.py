"""
vtelem - Test the correctness of primitive information.
"""

# module under test
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.enums.primitive import (
    Primitive,
    integer_can_hold,
    random_integer,
    INTEGER_PRIMITIVES,
)


def test_primitive_max_min():
    """Test that our internal representation of integers is correct."""

    # 8-bit
    assert Primitive.UINT8.value.max == 255
    assert Primitive.UINT8.value.min == 0
    assert Primitive.INT8.value.max == 127
    assert Primitive.INT8.value.min == -128

    # 16-bit
    assert Primitive.UINT16.value.max == 65535
    assert Primitive.UINT16.value.min == 0
    assert Primitive.INT16.value.max == 32767
    assert Primitive.INT16.value.min == -32768

    # 32-bit
    assert Primitive.UINT32.value.max == 4294967295
    assert Primitive.UINT32.value.min == 0
    assert Primitive.INT32.value.max == 2147483647
    assert Primitive.INT32.value.min == -2147483648

    # 64-bit
    assert Primitive.UINT64.value.max == 18446744073709551615
    assert Primitive.UINT64.value.min == 0
    assert Primitive.INT64.value.max == 9223372036854775807
    assert Primitive.INT64.value.min == -9223372036854775808

    assert integer_can_hold(Primitive.UINT8.value, 0)
    assert integer_can_hold(Primitive.UINT8.value, 255)

    # test random-integer generation
    for _ in range(1000):
        for prim in INTEGER_PRIMITIVES:
            assert integer_can_hold(prim.value, random_integer(prim))

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
