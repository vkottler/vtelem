"""
vtelem - A buffer implementation for serializing and de-serializing primitives.
"""

# built-in
from contextlib import contextmanager
import struct
from typing import Any, Iterator
import zlib

# internal
from vtelem.enums.primitive import Primitive, get_fstring, get_size


def crc(data: bytes, size: int = None, initial_val: int = 0) -> int:
    """Compute a generic 32-bit CRC."""

    if size is None:
        size = len(data)
    return zlib.crc32(data[0:size], initial_val)


class ByteBuffer:
    """
    A storage object useful for building network-transportable frames
    containing library primitives.
    """

    def __init__(
        self,
        data: bytearray = None,
        mutable: bool = True,
        size: int = 0,
        order: str = "!",
    ) -> None:
        """Construct a new, managed buffer."""

        if data is None:
            data = bytearray()
        self.size = size
        self.data = data
        self.pos: int = 0
        self.mutable = mutable
        self.order = order
        self.set_pos(0)

    def reset(self) -> None:
        """Re-initialize a mutable buffer to an empty one."""

        assert self.mutable
        self.data = bytearray()
        self.size = 0
        self.pos = 0

    @contextmanager
    def with_pos(self, pos: int = None) -> Iterator[None]:
        """
        A context manager for performing some operation on the buffer at a
        specific position, but restoring the original position when complete.
        """

        if pos is not None:
            orig_pos = self.get_pos()
        try:
            if pos is not None:
                self.set_pos(pos)
            yield
        finally:
            if pos is not None:
                self.set_pos(orig_pos)

    def expand_to(self, size: int) -> None:
        """Extend the backing buffer if requested."""

        if size > len(self.data):
            self.data += bytearray(size - len(self.data))

    def set_pos(self, pos: int) -> None:
        """Set the current buffer position."""

        # extend the backing buffer if position
        self.expand_to(pos)
        self.pos = pos

    def advance(self, amount: int, inc_size: bool = False) -> None:
        """Advance the current position by a specified amount."""

        self.set_pos(self.get_pos() + amount)
        if inc_size and (self.get_pos() > self.size):
            self.size += self.get_pos() - self.size

    def get_pos(self) -> int:
        """Obtain the current buffer position."""

        return self.pos

    def fstring(self, inst: Primitive) -> str:
        """
        Build the format String necessary for reading and writing the buffer.
        """

        return self.order + get_fstring(inst)

    @property
    def remaining(self) -> int:
        """Determine the amout of space (or data) remaining in the buffer."""

        return self.size - self.get_pos()

    def can_read(self, inst: Primitive) -> bool:
        """Determine if a specific primitive type can be read."""

        return self.remaining >= get_size(inst)

    def read(self, inst: Primitive, chomp: bool = False) -> Any:
        """Read a primitive out of a buffer, at its current position."""

        assert self.can_read(inst)
        result = struct.unpack(
            self.fstring(inst), self.read_bytes(get_size(inst), chomp)
        )[0]
        return result

    def read_bytes(self, count: int, chomp: bool = False) -> bytes:
        """Read some number of bytes from a buffer."""

        assert self.remaining >= count
        pos = self.get_pos()
        result = self.data[pos : pos + count]
        self.advance(count)

        # actually consume the bytes, can only be done from the front of the
        # buffer
        if chomp:
            assert pos == 0
            self.data = self.data[pos + count :]
            self.size = self.remaining
            self.set_pos(0)

        return result

    def append(self, other: bytes, data_len: int = None) -> int:
        """Add raw data to the end of this set."""

        if data_len is None:
            data_len = len(other)
        self.data = self.data[0 : self.size] + other[0:data_len]

        if not self.remaining and self.size != 0:
            self.advance(data_len, True)
        else:
            self.size += data_len

        return data_len

    def crc32(self, initial_val: int = 0) -> int:
        """Compute this buffer's crc32."""

        return crc(self.data, self.size, initial_val)

    def write(self, inst: Primitive, data: Any) -> int:
        """
        Write data of a specific primitive type into the buffer at its current
        position.
        """

        if not self.mutable:
            return 0
        size = get_size(inst)
        self.expand_to(self.get_pos() + size)
        struct.pack_into(self.fstring(inst), self.data, self.get_pos(), data)
        self.advance(size, True)
        return size
