"""
vtelem - Exposes a runtime environment for managing sets of channels.
"""

# built-in
from collections import defaultdict
import logging
from typing import Any, Dict, List, Optional, Tuple

# internal
from vtelem.channel import Channel
from vtelem.channel.framer import ChannelFramer
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes import LOG_PERIOD
from vtelem.classes.event_queue import EventQueue
from vtelem.classes.metered_queue import MeteredQueue
from vtelem.classes.time_entity import TimeEntity
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.enums.primitive import Primitive
from vtelem.frame.channel import ChannelFrame
from vtelem.parsing.encapsulation import ParsedFrame, decode_frame
from vtelem.registry import Registry

LOG = logging.getLogger(__name__)


class ChannelEnvironment(TimeEntity):
    """
    An environment for managing channels and building outgoing event and data
    frames.
    """

    def __init__(
        self,
        mtu: int,
        initial_channels: List[Channel] = None,
        metrics_rate: float = None,
        init_time: float = None,
        app_id_basis: float = None,
        use_crc: bool = True,
    ) -> None:
        """Construct a new channel environment."""

        TimeEntity.__init__(self, init_time)
        self.registries: Dict[str, Registry] = {}
        self.channel_registry = ChannelRegistry(initial_channels)
        self.registries["channel"] = self.channel_registry
        if initial_channels is None:
            initial_channels = []
        self.framer = ChannelFramer(
            mtu,
            self.channel_registry,
            initial_channels,
            self.lock,
            app_id_basis,
            use_crc,
        )
        self.write_crc = True

        self.metrics: Optional[Dict[str, int]] = None
        self.event_queue = EventQueue()
        if metrics_rate is not None:
            self.register_base_metrics(metrics_rate)
        self.frame_queue: MeteredQueue = MeteredQueue("frame", self)
        self.log_data: dict = defaultdict(lambda: 0.0)

    @property
    def app_id(self) -> TypePrimitive:
        """Get this environment's application identifier."""

        return self.framer.primitives["app_id"]

    def handle_new_mtu(self, new_mtu: int) -> None:
        """Set a new maximum transmission-unit size if necessary."""

        with self.lock:
            if new_mtu < self.framer.mtu:
                self.framer.mtu = new_mtu

    def register_base_metrics(self, metrics_rate: float) -> None:
        """Register standard environment metric channels."""

        if self.metrics is None:
            self.metrics = {}
            self.add_metric(
                "metrics_rate", Primitive.FLOAT, False, (metrics_rate, None)
            )
            self.add_metric("channel_count", Primitive.UINT32, True, (0, None))
            self.add_metric(
                "events_captured", Primitive.UINT32, True, (0, None)
            )
            self.add_metric(
                "emits_captured", Primitive.UINT32, True, (0, None)
            )
            self.add_metric(
                "dispatch_count", Primitive.UINT32, True, (0, None)
            )
            self.set_metric("channel_count", self.channel_registry.count())

    def has_metric(self, name: str) -> bool:
        """Check if a metric by a given name has already been registered."""

        return self.metrics is not None and name in self.metrics

    def add_metric(
        self,
        name: str,
        instance: Primitive,
        track_change: bool = False,
        initial: Tuple[Any, Optional[float]] = None,
    ) -> None:
        """Add a new, named metric channel"""

        if self.metrics is not None and not self.has_metric(name):
            self.metrics[name] = self.add_channel(
                name, instance, float(), track_change, initial, False
            )
            self.set_metric_rate(name, self.get_metric("metrics_rate"))

    def get_metric(self, name: str) -> Any:
        """Get the value from a metrics channel."""

        assert self.metrics is not None
        return self.get_value(self.metrics[name])

    def set_now(self, channel_id: int, data: Any) -> bool:
        """set a channel with the provided value, assign time."""

        chan = self.channel_registry.get_item(channel_id)
        assert chan is not None
        return chan.set(data, self.get_time())

    def get_value(self, chan_id: int) -> Any:
        """Get the current value of a channel, by integer identifier."""

        chan = self.channel_registry.get_item(chan_id)
        assert chan is not None
        return chan.get()

    def set_metric_rate(self, name: str, rate: float) -> None:
        """Set the rate of a metrics channel."""

        if self.metrics is not None:
            self.set_channel_rate(self.metrics[name], rate)

    def set_metric(self, name: str, data: Any, time: float = None) -> None:
        """Set a metric channel to a specific value"""

        if self.metrics is not None and name in self.metrics:
            chan = self.channel_registry.get_item(self.metrics[name])
            assert chan is not None
            assert chan.set(data, time)

    def metric_add(self, name: str, data: Any, time: float = None) -> None:
        """Add a value to a metric channel."""

        if self.metrics is not None and name in self.metrics:
            chan = self.channel_registry.get_item(self.metrics[name])
            assert chan is not None
            assert chan.add(data, time)

    def set_channel_rate(self, chan_id: int, rate: float) -> None:
        """Set the update-rate of a channel."""

        chan = self.channel_registry.get_item(chan_id)
        assert chan is not None
        chan.set_rate(rate)

    def has_channel(self, name: str) -> bool:
        """A quick check that this environmentl has a named channel."""

        chan_id = self.channel_registry.get_id(name)
        return chan_id is not None

    def command_channel_id(self, chan_id: int, value: Any) -> bool:
        """Attempt to command a channel, by its integer identifier."""

        chan = self.channel_registry.get_item(chan_id)
        assert chan is not None
        with self.lock:
            result = chan.command(value, self.get_time())
        return result

    def command_channel(self, name: str, value: Any) -> bool:
        """Attempt to command a channel, by its name."""

        if not self.has_channel(name):
            return False
        chan_id = self.channel_registry.get_id(name)
        assert chan_id is not None
        return self.command_channel_id(chan_id, value)

    def add_channel(
        self,
        name: str,
        instance: Primitive,
        rate: float,
        track_change: bool = False,
        initial: Tuple[Any, Optional[float]] = None,
        commandable: bool = True,
    ) -> int:
        """
        Register a channel with the environment, returns an integer identifier
        that can be used to set the channel's value through the environment.
        """

        with self.lock:
            queue = None if not track_change else self.event_queue
            new_chan = Channel(name, instance, rate, queue, commandable)
            if initial is not None:
                assert new_chan.set(initial[0], initial[1])
            result = self.channel_registry.add_channel(new_chan)
            assert result[0]
            self.framer.add_channel(new_chan)

        self.metric_add("channel_count", 1)
        return result[1]

    def dispatch(self, time: float, should_log: bool = True) -> int:
        """Dispatch events and channel emissions."""

        with self.lock:
            data = self.dispatch_data(time)
            events = self.dispatch_events(time)
            self.metric_add("dispatch_count", 1)

        total = data[0] + events[0]

        self.log_data["emits"] += data[1]
        self.log_data["events"] += events[1]
        self.log_data["frames"] += total

        if should_log:
            if time - self.log_data["last_log"] >= LOG_PERIOD:
                LOG.info(
                    "%.3f: %d emits, %d events, %d frames",
                    time,
                    self.log_data["emits"],
                    self.log_data["events"],
                    self.log_data["frames"],
                )
                self.log_data["emits"] = 0
                self.log_data["events"] = 0
                self.log_data["frames"] = 0
                self.log_data["last_log"] = time

        return total

    def get_next_frame(self, timeout: int = 5) -> ChannelFrame:
        """Get the next available frame from the queue."""

        return self.frame_queue.get(timeout=timeout)

    def decode_frame(
        self,
        data: bytes,
        size: int,
        expected_id: Optional[TypePrimitive] = None,
    ) -> Optional[ParsedFrame]:
        """Unpack a frame from an array of bytes."""

        return decode_frame(self.channel_registry, data, size, expected_id)

    def dispatch_events(self, time: float) -> Tuple[int, int]:
        """Process all queued events (build frames)."""

        result = self.framer.build_event_frames(
            time, self.event_queue, self.frame_queue, self.write_crc
        )
        self.metric_add("events_captured", result[1], time)
        return result

    def dispatch_data(self, time: float) -> Tuple[int, int]:
        """Process all channel emissions for the specified, absolute time."""

        result = self.framer.build_data_frames(
            time, self.frame_queue, self.write_crc
        )
        self.metric_add("emits_captured", result[1], time)
        return result

    def dispatch_now(self, *_, should_log: bool = True, **__) -> int:
        """Dispatch telemetry at the current time."""

        return self.dispatch(self.get_time(), should_log)
