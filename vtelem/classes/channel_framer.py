
"""
vtelem - A module for building frames of channel data from emissions.
"""

# built-in
from typing import List

# internal
from vtelem.enums.primitive import Primitive
from .channel import Channel
from .channel_frame import ChannelFrame
from .channel_registry import ChannelRegistry
from .type_primitive import TypePrimitive

TIMESTAMP_PRIM = Primitive.UINT64


class ChannelFramer:
    """
    An extension of channel management that builds frames from emitted data.
    """

    def __init__(self, mtu: int, registry: ChannelRegistry,
                 channels: List[Channel]) -> None:
        """ Construct a new channel framer. """

        self.mtu = mtu
        self.registry = registry
        self.channels = channels
        self.timestamp = TypePrimitive(TIMESTAMP_PRIM)

    def new_frame(self, time: float, set_time: bool = True) -> ChannelFrame:
        """ Construct a new frame object. """

        if set_time:
            assert self.timestamp.set(time)
        return ChannelFrame(self.mtu, self.timestamp)

    def build_frames(self, time: float) -> List[ChannelFrame]:
        """
        For this step, gather up channel emissions into discrete frames for
        wire-level transport.
        """

        frames = []
        emit_count = 0
        curr_frame = self.new_frame(time)

        for channel in self.channels:

            result = channel.emit(time)

            # if the channel emitted, add it to the current frame
            if result is not None:
                emit_count += 1

                chan_id = self.registry.get_id(channel.name)
                assert chan_id is not None

                # if we failed to add this emit to the current frame, finalize
                # it and start a new one
                if not curr_frame.add(chan_id, channel.type, result):
                    curr_frame.finalize()
                    frames.append(curr_frame)
                    curr_frame = self.new_frame(time, False)
                    assert curr_frame.add(chan_id, channel.type, result)

        # finalize the last frame if necessary
        if emit_count and not curr_frame.finalized:
            curr_frame.finalize()
            frames.append(curr_frame)

        return frames
