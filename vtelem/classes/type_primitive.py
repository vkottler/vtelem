
"""
vtelem - A generic element that can be read from and written to buffers.
"""

# built-in
from typing import Any

# internal
from vtelem.enums.primitive import Primitive, default_val, get_size
from .byte_buffer import ByteBuffer


class TypePrimitive:
    """
    A class for storing primitive data types that can be read from and written
    into buffers.
    """

    def __init__(self, instance: Primitive):
        """ Construct a new primitive storage of a certain type. """

        self.type = instance
        self.data: Any = default_val(self.type)

    def set(self, data: Any) -> bool:
        """ Set this primitive's data manually. """

        if isinstance(data, self.type.value["type"]):
            self.data = self.type.value["type"](data)
            return True
        return False

    def get(self) -> Any:
        """ Get this primitive's data. """

        return self.data

    def size(self) -> int:
        """ Get the size of this primitive type. """

        return get_size(self.type)

    def write(self, buf: ByteBuffer, pos: int = None) -> bool:
        """ Write this primitive into a buffer. """

        with buf.with_pos(pos):
            result = buf.write(self.type, self.data)
        return result

    def read(self, buf: ByteBuffer, pos: int = None) -> Any:
        """
        Read this primitive out of a buffer, assign its data and return the
        result.
        """

        with buf.with_pos(pos):
            result = buf.read(self.type)
        self.data = result
        return result
