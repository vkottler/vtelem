
"""
vtelem - Exposes a runtime environment for managing sets of channels.
"""

# built-in
import logging
from typing import Any, List, Tuple, Dict, Optional
from queue import Queue

# internal
from vtelem.enums.primitive import Primitive
from vtelem.parsing import parse_data_frame, parse_event_frame
from . import TIMESTAMP_PRIM, COUNT_PRIM, ENUM_TYPE
from .byte_buffer import ByteBuffer
from .channel import Channel
from .channel_registry import ChannelRegistry
from .channel_frame import ChannelFrame
from .channel_framer import ChannelFramer, FRAME_TYPES
from .event_queue import EventQueue
from .time_entity import TimeEntity

LOG = logging.getLogger(__name__)


class ChannelEnvironment(TimeEntity):
    """
    An environment for managing channels and building outgoing event and data
    frames.
    """

    def __init__(self, mtu: int, initial_channels: List[Channel] = None,
                 metrics_rate: float = None, init_time: float = None) -> None:
        """ Construct a new channel environment. """

        super().__init__(init_time)
        self.channel_registry = ChannelRegistry(initial_channels)
        if initial_channels is None:
            initial_channels = []
        self.framer = ChannelFramer(mtu, self.channel_registry,
                                    initial_channels)
        self.event_queue = EventQueue()
        self.frame_queue: Queue = Queue()

        self.metrics: Optional[Dict[str, int]] = None
        if metrics_rate is not None:
            self.metrics = {}
            self.add_metric("metrics_rate", Primitive.FLOAT, False,
                            (metrics_rate, None))
            self.add_metric("channel_count", Primitive.UINT32, True,
                            (0, None))
            self.add_metric("frames_created", Primitive.UINT32, True,
                            (0, None))
            self.add_metric("frames_consumed", Primitive.UINT32, True,
                            (0, None))
            self.add_metric("events_captured", Primitive.UINT32, True,
                            (0, None))
            self.add_metric("emits_captured", Primitive.UINT32, True,
                            (0, None))
            self.add_metric("dispatch_count", Primitive.UINT32, True,
                            (0, None))
            self.set_metric("channel_count", self.channel_registry.count())

    def add_metric(self, name: str, instance: Primitive,
                   track_change: bool = False,
                   initial: Tuple[Any, Optional[float]] = None) -> None:
        """ Add a new, named metric channel """

        assert self.metrics is not None
        assert name not in self.metrics
        self.metrics[name] = self.add_channel(name, instance, float(),
                                              track_change, initial)
        self.set_metric_rate(name, self.get_metric("metrics_rate"))

    def get_metric(self, name: str) -> Any:
        """ Get the value from a metrics channel. """

        assert self.metrics is not None
        return self.get_value(self.metrics[name])

    def get_value(self, chan_id: int) -> Any:
        """ Get the current value of a channel, by integer identifier. """

        chan = self.channel_registry.get_item(chan_id)
        assert chan is not None
        return chan.get()

    def set_metric_rate(self, name: str, rate: float) -> None:
        """ Set the rate of a metrics channel. """

        assert self.metrics is not None
        self.set_channel_rate(self.metrics[name], rate)

    def set_metric(self, name: str, data: Any, time: float = None) -> None:
        """ Set a metric channel to a specific value """

        assert self.metrics is not None
        if name in self.metrics:
            chan = self.channel_registry.get_item(self.metrics[name])
            assert chan is not None
            assert chan.set(data, time)

    def metric_add(self, name: str, data: Any, time: float = None) -> None:
        """ Add a value to a metric channel. """

        assert self.metrics is not None
        if name in self.metrics:
            chan = self.channel_registry.get_item(self.metrics[name])
            assert chan is not None
            assert chan.add(data, time)

    def set_channel_rate(self, chan_id: int, rate: float) -> None:
        """ Set the update-rate of a channel. """

        chan = self.channel_registry.get_item(chan_id)
        assert chan is not None
        chan.set_rate(rate)

    def add_channel(self, name: str, instance: Primitive, rate: float,
                    track_change: bool = False,
                    initial: Tuple[Any, Optional[float]] = None) -> int:
        """
        Register a channel with the environment, returns an integer identifier
        that can be used to set the channel's value through the environment.
        """

        with self.lock:
            queue = None if not track_change else self.event_queue
            new_chan = Channel(name, instance, rate, queue)
            if initial is not None:
                assert new_chan.set(initial[0], initial[1])
            result = self.channel_registry.add_channel(new_chan)
            assert result[0]
            self.framer.add_channel(new_chan)
        if self.metrics is not None:
            self.metric_add("channel_count", 1)
        return result[1]

    def dispatch(self, time: float, should_log: bool = True) -> int:
        """ Dispatch events and channel emissions. """

        with self.lock:
            data = self.dispatch_data(time)
            events = self.dispatch_events(time)
            if self.metrics is not None:
                self.metric_add("dispatch_count", 1)
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

        frame = self.frame_queue.get()
        if self.metrics is not None:
            self.metric_add("frames_consumed", 1)
        return frame

    def decode_frame(self, data: bytearray, size: int) -> dict:
        """ Unpack a frame from an array of bytes. """

        result = {}
        buf = ByteBuffer(data, False, size)

        # read header
        result["type"] = FRAME_TYPES.get_str(buf.read(ENUM_TYPE))
        result["timestamp"] = buf.read(TIMESTAMP_PRIM)
        result["size"] = buf.read(COUNT_PRIM)

        # read channel IDs
        if result["type"] == "DATA":
            parse_data_frame(result, buf, self.channel_registry)
        elif result["type"] == "EVENT":
            parse_event_frame(result, buf, self.channel_registry)

        return result

    def dispatch_events(self, time: float) -> Tuple[int, int]:
        """ Process all queued events (build frames). """

        result = self.framer.build_event_frames(time, self.event_queue,
                                                self.frame_queue)
        if self.metrics is not None:
            self.metric_add("frames_created", result[0], time)
            self.metric_add("events_captured", result[1], time)
        return result

    def dispatch_data(self, time: float) -> Tuple[int, int]:
        """ Process all channel emissions for the specified, absolute time. """

        result = self.framer.build_data_frames(time, self.frame_queue)
        if self.metrics is not None:
            self.metric_add("frames_created", result[0], time)
            self.metric_add("emits_captured", result[1], time)
        return result
