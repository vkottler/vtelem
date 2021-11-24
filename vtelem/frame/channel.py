"""
vtelem - A module that implements storage for channel data, restricted by
         a desired maximum size.
"""

# built-in
from typing import Any

# internal
from vtelem.classes import DEFAULTS, EventType
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.enums.primitive import Primitive, get_size
from vtelem.frame import Frame, time_to_int


class ChannelFrame(Frame):
    """A channel-data storage that respects a maximum size."""

    def __init__(
        self,
        mtu: int,
        frame_id: TypePrimitive,
        frame_type: TypePrimitive,
        timestamp: TypePrimitive,
        use_crc: bool = True,
    ) -> None:
        """Construct an empty channel frame."""

        super().__init__(mtu, frame_id, frame_type, timestamp, use_crc)
        self.elem_buffer = ByteBuffer(bytearray(self.mtu))

    def finalize_hook(self) -> None:
        """Append the element buffer to the actual frame buffer."""

        self.buffer.append(self.elem_buffer.data, self.elem_buffer.size)
        self.initialized = True

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
        space_required += 2 * get_size(DEFAULTS["timestamp"])
        if (self.used + space_required > self.mtu) or self.finalized:
            return False

        # write the channel identifier into the real buffer
        assert self.id_primitive.set(chan_id)
        self.used += self.id_primitive.write(self.buffer)

        # write the event data into the element buffer
        data_prim = TypePrimitive(chan_type)
        time_prim = new_default("timestamp")

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

        self.increment_count()
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
        self.write(self.id_primitive)

        # write the channel value into the element buffer
        self.used += self.elem_buffer.write(chan_type, chan_val)

        self.increment_count()
        return True
