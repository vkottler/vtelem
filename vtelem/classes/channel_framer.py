
"""
vtelem - A module for building frames of channel data from emissions.
"""

# built-in
from queue import Queue
from typing import Dict, Tuple, List

# internal
from . import TIMESTAMP_PRIM
from .channel import Channel
from .channel_frame import ChannelFrame, time_to_int
from .channel_registry import ChannelRegistry
from .event_queue import EventQueue
from .type_primitive import TypePrimitive
from .user_enum import UserEnum

FRAME_TYPES = UserEnum("frame_type",
                       {0: "INVALID", 1: "DATA", 2: "EVENT"})


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
        self.frame_types = FRAME_TYPES

        # build primitives to hold the frame types and timestamps
        self.timestamps: Dict[str, TypePrimitive] = {}
        self.primitives: Dict[str, TypePrimitive] = {}
        for name in FRAME_TYPES.enum.values():
            self.timestamps[name] = TypePrimitive(TIMESTAMP_PRIM)
            self.primitives[name] = self.frame_types.get_primitive(name)

    def get_types(self) -> UserEnum:
        """ Get the frame-type enumeration. """

        return self.frame_types

    def new_frame(self, frame_type: str, time: float,
                  set_time: bool = True) -> ChannelFrame:
        """ Construct a new frame object. """

        timestamp = self.timestamps[frame_type]
        if set_time:
            assert timestamp.set(time_to_int(time))
        return ChannelFrame(self.mtu, self.primitives[frame_type], timestamp)

    def new_event_frame(self, time: float,
                        set_time: bool = True) -> ChannelFrame:
        """ Construct a new event-frame object. """

        return self.new_frame("EVENT", time, set_time)

    def new_data_frame(self, time: float,
                       set_time: bool = True) -> ChannelFrame:
        """ Construct a new data-frame object. """

        return self.new_frame("DATA", time, set_time)

    def add_channel(self, channel: Channel) -> None:
        """ Add another managed channel. """

        self.channels.append(channel)

    def build_event_frames(self, time: float, event_queue: EventQueue,
                           queue: Queue) -> Tuple[int, int]:
        """
        Consume the current event queue and build frames from the contained
        events.
        """

        frame_count = 0
        events = event_queue.consume()
        event_count = len(events)

        curr_frame = self.new_event_frame(time)
        for event in events:
            chan_id = self.registry.get_id(event[0])
            assert chan_id is not None
            chan_type = self.registry.get_channel_type(chan_id)

            # add this event, start a new frame if necessary
            if not curr_frame.add_event(chan_id, chan_type, event[1],
                                        event[2]):
                curr_frame.finalize()
                queue.put(curr_frame)
                frame_count += 1
                curr_frame = self.new_event_frame(time, False)
                assert curr_frame.add_event(chan_id, chan_type, event[1],
                                            event[2])

        # finalize the last frame if necessary
        if event_count and not curr_frame.finalized:
            curr_frame.finalize()
            queue.put(curr_frame)
            frame_count += 1

        return (frame_count, event_count)

    def build_data_frames(self, time: float, queue: Queue) -> Tuple[int, int]:
        """
        For this step, gather up channel emissions into discrete frames for
        wire-level transport.
        """

        frame_count = 0
        emit_count = 0

        curr_frame = self.new_data_frame(time)
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
                    queue.put(curr_frame)
                    frame_count += 1
                    curr_frame = self.new_data_frame(time, False)
                    assert curr_frame.add(chan_id, channel.type, result)

        # finalize the last frame if necessary
        if emit_count and not curr_frame.finalized:
            curr_frame.finalize()
            queue.put(curr_frame)
            frame_count += 1

        return (frame_count, emit_count)