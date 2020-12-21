
"""
vtelem - A buffer implementation for serializing and de-serializing primitives.
"""

# built-in
from contextlib import contextmanager
import struct
import threading
from typing import Any, Iterator

# internal
from vtelem.enums.primitive import Primitive, get_size, get_fstring


class ByteBuffer:
    """
    A storage object useful for building network-transportable frames
    containing library primitives.
    """

    def __init__(self, data: bytearray = None, mutable: bool = True,
                 order: str = "!") -> None:
        """ Construct a new, managed buffer """

        if data is None:
            data = bytearray()
        self.data = data
        self.pos: int = 0
        self.size: int = 0
        self.mutable = mutable
        self.order = order
        self.lock = threading.RLock()
        self.set_pos(0)

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
        """ Extend the backing buffer if requested. """

        if size > len(self.data):
            with self.lock:
                self.data += bytearray(size - len(self.data))

    def set_pos(self, pos: int) -> None:
        """ Set the current buffer position. """

        with self.lock:
            # extend the backing buffer if position
            self.expand_to(pos + 1)
            self.pos = pos

    def advance(self, amount: int, inc_size: bool = False) -> None:
        """ Advance the current position by a specified amount. """

        with self.lock:
            self.set_pos(self.get_pos() + amount)
            if inc_size:
                self.size += amount

    def get_pos(self) -> int:
        """ Obtain the current buffer position. """

        return self.pos

    def fstring(self, inst: Primitive) -> str:
        """
        Build the format String necessary for reading and writing the buffer.
        """

        return self.order + get_fstring(inst)

    def read(self, inst: Primitive) -> Any:
        """ Read a primitive out of a buffer, at its current position. """

        with self.lock:
            end_pos = self.get_pos() + get_size(inst)
            buffer_slice = self.data[self.get_pos():end_pos]
            result = struct.unpack(self.fstring(inst), buffer_slice)[0]
            self.advance(get_size(inst))
        return result

    def append(self, other: bytearray, data_len: int) -> None:
        """ Add raw data to the end of this set. """

        with self.lock:
            self.data = self.data[0:self.size] + other
            self.size += data_len

    def write(self, inst: Primitive, data: Any) -> int:
        """
        Write data of a specific primitive type into the buffer at its current
        position.
        """

        if not self.mutable:
            return 0
        with self.lock:
            size = get_size(inst)
            self.expand_to(self.get_pos() + size)
            struct.pack_into(self.fstring(inst), self.data, self.get_pos(),
                             data)
            self.advance(size, True)
        return size
