"""
vtelem - Test the byte-buffer class's correctness.
"""

# module under test
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.enums.primitive import Primitive


def test_byte_buffer_basic():
    """Test basic read and write operations with a byte buffer."""

    buf = ByteBuffer()

    type_a = TypePrimitive(Primitive.BOOL)
    assert not type_a.set("test")
    assert not type_a.set(5)
    assert type_a.set(True)
    assert type_a.set(False)
    assert type_a.set(True)

    type_b = TypePrimitive(Primitive.INT32)
    assert not type_b.set("test")
    assert type_b.set(255)

    type_c = TypePrimitive(Primitive.FLOAT)
    assert not type_c.set("test")
    assert type_c.set(3.14)

    type_a.write(buf)
    type_b.write(buf)
    type_c.write(buf)

    buf.set_pos(0)

    assert type_a.get() == type_a.read(buf)
    assert type_b.get() == type_b.read(buf)
    assert abs(type_c.get() - type_c.read(buf)) < 0.001

    assert type_a.get() == type_a.read(buf, 0)
    assert type_b.get() == type_b.read(buf, type_a.size())
    c_pos = type_a.size() + type_b.size()
    assert abs(type_c.get() - type_c.read(buf, c_pos)) < 0.001

    buf.append(bytearray(10), 10)

    immut_buf = ByteBuffer(mutable=False)
    assert not immut_buf.write(Primitive.BOOL, False)
