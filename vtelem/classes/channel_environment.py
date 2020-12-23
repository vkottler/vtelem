
"""
vtelem - Exposes a runtime environment for managing sets of channels.
"""

# built-in
import logging
from typing import List, Tuple
from queue import Queue
import threading

# internal
from vtelem.enums.primitive import Primitive
from .channel import Channel
from .channel_registry import ChannelRegistry
from .channel_frame import ChannelFrame
from .channel_framer import ChannelFramer
from .event_queue import EventQueue

LOG = logging.getLogger(__name__)


class ChannelEnvironment:
    """
    An environment for managing channels and building outgoing event and data
    frames.
    """

    def __init__(self, mtu: int,
                 initial_channels: List[Channel] = None) -> None:
        """ Construct a new channel environment. """

        self.channel_registry = ChannelRegistry(initial_channels)
        if initial_channels is None:
            initial_channels = []
        self.framer = ChannelFramer(mtu, self.channel_registry,
                                    initial_channels)
        self.event_queue = EventQueue()
        self.frame_queue: Queue = Queue()
        self.lock = threading.RLock()

    def add_channel(self, name: str, instance: Primitive, rate: float,
                    track_change: bool = False) -> int:
        """
        Register a channel with the environment, returns an integer identifier
        that can be used to set the channel's value through the environment.
        """

        with self.lock:
            queue = None if not track_change else self.event_queue
            new_chan = Channel(name, instance, rate, queue)
            result = self.channel_registry.add_channel(new_chan)
            assert result[0]
            self.framer.add_channel(new_chan)
        return result[1]

    def dispatch(self, time: float, should_log: bool = True) -> int:
        """ Dispatch events and channel emissions. """

        with self.lock:
            data = self.dispatch_data(time)
            events = self.dispatch_events(time)
        if data[1] and should_log:
            LOG.debug("%.3f: %d emits", time, data[1])
        if events[1] and should_log:
            LOG.debug("%.3f: %d events", time, events[1])
        total = data[0] + events[0]
        if total and should_log:
            LOG.debug("%.3f: %d frames", time, total)
        return total

    def get_next_frame(self) -> ChannelFrame:
        """ Get the next available frame from the queue. """

        return self.frame_queue.get()

    def dispatch_events(self, time: float) -> Tuple[int, int]:
        """ Process all queued events (build frames). """

        return self.framer.build_event_frames(time, self.event_queue,
                                              self.frame_queue)

    def dispatch_data(self, time: float) -> Tuple[int, int]:
        """ Process all channel emissions for the specified, absolute time. """

        return self.framer.build_data_frames(time, self.frame_queue)
