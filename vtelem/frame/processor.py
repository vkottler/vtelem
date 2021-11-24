"""
vtelem - A module providing utilities for parsing frames.
"""

# built-in
from typing import List, cast

# internal
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.type_primitive import TypePrimitive


class FrameProcessor:
    """
    A class exposing an interface for processing a stream of bytes as coherent
    sequences of bytes that can be further parsed as frames.
    """

    def __init__(self) -> None:
        """Construct a new message processor."""

        self.buffer = ByteBuffer()
        self.size: int = 0
        self.size_stale: bool = True

    def read_size(self, frame_size: TypePrimitive, mtu: int) -> None:
        """
        Attempt to process the next 'length' parameter of a frame header, if
        successful the buffer can be further processes as a frame (if it
        contains enough bytes yet).
        """

        if self.size_stale and self.buffer.can_read(frame_size.type):
            self.size = cast(int, frame_size.read(self.buffer, chomp=True))
            self.size_stale = False

        # clear buffer state if we get an unreasonable value
        if self.size > mtu:
            self.buffer.reset()
            self.size_stale = True

    def process(
        self, data: bytes, frame_size: TypePrimitive, mtu: int
    ) -> List[bytes]:
        """
        Process a new set of bytes and return a list of byte sequences that
        can be coherently processed as frames.
        """

        result: List[bytes] = []
        self.buffer.append(data)

        self.read_size(frame_size, mtu)

        # read the size of the next frame, then the frame-data itself
        while not self.size_stale and self.size <= self.buffer.remaining:
            result.append(self.buffer.read_bytes(self.size, True))
            self.size_stale = True
            self.read_size(frame_size, mtu)

        return result
