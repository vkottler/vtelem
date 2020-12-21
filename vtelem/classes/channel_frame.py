
"""
vtelem - A module that implements storage for channel data, restricted by
         a desired maximum size.
"""

# built-in
from typing import Any, Dict

# internal
from vtelem.enums.primitive import Primitive, get_size
from .byte_buffer import ByteBuffer
from .type_primitive import TypePrimitive

COUNT_PRIM = Primitive.UINT32
ID_PRIM = Primitive.UINT16


class ChannelFrame:
    """ A channel-data storage that respects a maximum size. """

    def __init__(self, mtu: int, timestamp: TypePrimitive) -> None:
        """ Construct an empty channel frame. """

        self.mtu = mtu
        self.used: int = 0
        self.buffer = ByteBuffer(bytearray(self.mtu))
        self.elem_buffer = ByteBuffer()
        self.id_primitive = TypePrimitive(ID_PRIM)
        self.finalized = False

        # write frame header: timestamp
        self.used += timestamp.write(self.buffer)

        # write frame header: element count (placeholder)
        self.count: Dict[str, Any] = {}
        self.count["primitive"] = TypePrimitive(COUNT_PRIM)
        self.count["position"] = self.buffer.get_pos()
        self.count["value"] = 0
        self.used += self.count["primitive"].write(self.buffer)

        assert self.used < self.mtu

    def finalize(self) -> int:
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
        self.finalized = True
        return self.used

    def add(self, chan_id: int, chan_type: Primitive, chan_val: Any) -> bool:
        """
        Add a channel element into the frame, returns True on success or False
        if there wasn't enough space.
        """

        space_required = self.id_primitive.size() + get_size(chan_type)
        if (self.used + space_required > self.mtu) or self.finalized:
            return False

        # write the channel ID into the real buffer
        assert self.id_primitive.set(chan_id)
        self.used += self.id_primitive.write(self.buffer)

        # write the channel value into the element buffer
        self.used += self.elem_buffer.write(chan_type, chan_val)

        self.count["value"] += 1

        return True
