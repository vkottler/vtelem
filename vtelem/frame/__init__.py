"""
vtelem - A module for basic frame interfaces.
"""

# built-in
import math
from typing import Any, Dict, Tuple

# internal
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.enums.primitive import random_integer

FRAME_OVERHEAD = new_default("count").type.value.size


def time_to_int(time: float, precision: int = 1000) -> int:
    """Convert a floating-point time value into an integer."""

    frac, num = math.modf(time)
    return int((int(num) * precision) + int(math.floor(frac * precision)))


class Frame:
    """A base class for frames."""

    def __init__(
        self,
        mtu: int,
        frame_id: TypePrimitive,
        frame_type: TypePrimitive,
        timestamp: TypePrimitive,
        use_crc: bool = True,
    ) -> None:
        """Construct an empty frame."""

        self.mtu = mtu
        self.used: int = 0
        self.buffer = ByteBuffer(bytearray(self.mtu))
        self.id_primitive = new_default("id")
        self.finalized = False
        self.initialized = False

        # write frame header: (application) id, type, timestamp
        self.write(frame_id)
        self.write(frame_type)
        self.write(timestamp)

        # write frame header: element count (placeholder)
        self.count: Dict[str, Any] = {}
        self.count["primitive"] = new_default("count")
        self.count["position"] = self.buffer.get_pos()
        self.count["value"] = 0
        self.write(self.count["primitive"])

        # reserve space for crc
        self.crc = None
        if use_crc:
            self.crc = new_default("crc")
            self.used += self.crc.size()
        self.overhead = self.used

        assert self.space > 0

    def write(self, elem: TypePrimitive) -> None:
        """Write a primitive into the buffer."""

        self.used += elem.write(self.buffer)

    @property
    def space(self) -> int:
        """Get the amount of space left in this frame."""

        return self.mtu - self.used

    def increment_count(self, amount: int = 1) -> None:
        """Increment this frame's count by some amount."""

        self.count["value"] += amount

    def pad(self, num_bytes: int) -> int:
        """
        Attempt to add padding bytes at the end of a frame, return the actual
        amout of padding added.
        """

        # only allow padding at the end of a frame
        assert self.finalized

        # don't allow more padding outside the mtu
        pad_amt = min(num_bytes, self.mtu - self.used)
        self.buffer.append(bytearray(pad_amt), pad_amt)
        self.used += pad_amt
        return pad_amt

    def pad_to_mtu(self) -> None:
        """Attempt to pad this frame to the full mtu size."""

        self.pad(self.mtu - self.used)

    @property
    def raw(self) -> Tuple[bytearray, int]:
        """Obtain the raw buffer, and its size, from this frame."""

        assert self.finalized
        return self.buffer.data, self.used

    def with_size_header(
        self, frame_size: TypePrimitive = None
    ) -> Tuple[bytes, int]:
        """
        Get a buffer (and its size) for this frame, with the inter-frame
        size header included.
        """

        if frame_size is None:
            frame_size = new_default("count")

        data, size = self.raw
        assert frame_size.set(size)
        return frame_size.buffer() + data, size + frame_size.type.value.size

    def finalize_hook(self) -> None:
        """Can be overridden by implementing classes."""

    def finalize(self, write_crc: bool = True) -> int:
        """
        Finalize this frame, making the underlying buffer ready for wire-level
        transport.
        """

        if self.finalized:
            return self.used

        # write the count into the frame, into its reserved position
        assert self.count["primitive"].set(self.count["value"])
        self.count["primitive"].write(self.buffer, self.count["position"])

        # run frame-specific finalization
        self.finalize_hook()
        assert self.initialized

        # compute and write the crc
        if self.crc is not None:
            if write_crc:
                self.crc.set(self.buffer.crc32())
            else:
                self.crc.set(random_integer(self.crc.type))
            self.crc.write(self.buffer)

        self.finalized = True
        assert self.buffer.size == self.used
        return self.used
