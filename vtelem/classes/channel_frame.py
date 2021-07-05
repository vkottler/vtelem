"""
vtelem - A module that implements storage for channel data, restricted by
         a desired maximum size.
"""

# built-in
import math
from typing import Any, Dict, Tuple

# internal
from vtelem.enums.primitive import Primitive, get_size, random_integer
from . import COUNT_PRIM, ID_PRIM, TIMESTAMP_PRIM, EventType
from .byte_buffer import ByteBuffer
from .type_primitive import TypePrimitive


def time_to_int(time: float, precision: int = 1000) -> int:
    """Convert a floating-point time value into an integer."""

    frac, num = math.modf(time)
    return int((int(num) * precision) + int(math.floor(frac * precision)))


class ChannelFrame:
    """A channel-data storage that respects a maximum size."""

    def __init__(
        self,
        mtu: int,
        frame_id: TypePrimitive,
        frame_type: TypePrimitive,
        timestamp: TypePrimitive,
    ) -> None:
        """Construct an empty channel frame."""

        self.mtu = mtu
        self.used: int = 0
        self.buffer = ByteBuffer(bytearray(self.mtu))
        self.elem_buffer = ByteBuffer(bytearray(self.mtu))
        self.id_primitive = TypePrimitive(ID_PRIM)
        self.finalized = False

        # write frame header: (application) id, type, timestamp
        self.used += frame_id.write(self.buffer)
        self.used += frame_type.write(self.buffer)
        self.used += timestamp.write(self.buffer)

        # write frame header: element count (placeholder)
        self.count: Dict[str, Any] = {}
        self.count["primitive"] = TypePrimitive(COUNT_PRIM)
        self.count["position"] = self.buffer.get_pos()
        self.count["value"] = 0
        self.used += self.count["primitive"].write(self.buffer)

        # reserve space for crc
        self.crc = TypePrimitive(Primitive.UINT32)
        self.used += self.crc.size()

        assert self.used < self.mtu

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

        # add the element buffer to the end of our current frame buffer
        self.buffer.append(self.elem_buffer.data, self.elem_buffer.size)

        # compute and write the crc
        if write_crc:
            self.crc.set(self.buffer.crc32())
        else:
            self.crc.set(random_integer(self.crc.type))
        self.crc.write(self.buffer)

        self.finalized = True
        assert self.buffer.size == self.used
        return self.used

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

    def raw(self) -> Tuple[bytearray, int]:
        """Obtain the raw buffer, and its size, from this frame."""

        assert self.finalized
        return self.buffer.data, self.used

    def add_event(
        self,
        chan_id: int,
        chan_type: Primitive,
        prev: EventType,
        curr: EventType,
    ) -> bool:
        """Add event data into this frame."""

        # determine if this event element will fit in the current frame
        space_required = self.id_primitive.size()
        space_required += 2 * get_size(chan_type)
        space_required += 2 * get_size(TIMESTAMP_PRIM)
        if (self.used + space_required > self.mtu) or self.finalized:
            return False

        # write the channel identifier into the real buffer
        assert self.id_primitive.set(chan_id)
        self.used += self.id_primitive.write(self.buffer)

        # write the event data into the element buffer
        data_prim = TypePrimitive(chan_type)
        time_prim = TypePrimitive(TIMESTAMP_PRIM)

        # write 'prev'
        data_prim.set(prev[0])
        self.used += data_prim.write(self.elem_buffer)
        time_prim.set(time_to_int(prev[1]))
        self.used += time_prim.write(self.elem_buffer)

        # write 'curr'
        data_prim.set(curr[0])
        self.used += data_prim.write(self.elem_buffer)
        time_prim.set(time_to_int(curr[1]))
        self.used += time_prim.write(self.elem_buffer)

        self.count["value"] += 1
        return True

    def add(self, chan_id: int, chan_type: Primitive, chan_val: Any) -> bool:
        """
        Add a channel element into the frame, returns True on success or False
        if there wasn't enough space.
        """

        space_required = self.id_primitive.size() + get_size(chan_type)
        if (self.used + space_required > self.mtu) or self.finalized:
            return False

        # write the channel identifier into the real buffer
        assert self.id_primitive.set(chan_id)
        self.used += self.id_primitive.write(self.buffer)

        # write the channel value into the element buffer
        self.used += self.elem_buffer.write(chan_type, chan_val)

        self.count["value"] += 1
        return True
