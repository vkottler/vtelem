
"""
vtelem - An environment that supports management of telemetry.
"""

# built-in
from collections import defaultdict
from enum import Enum
from typing import List, Dict, Type, Tuple, Optional

# internal
from vtelem.enums.primitive import Primitive
from . import ENUM_TYPE
from .channel import Channel
from .channel_environment import ChannelEnvironment
from .enum_registry import EnumRegistry
from .user_enum import UserEnum, from_enum
from .type_registry import get_default


class TelemetryEnvironment(ChannelEnvironment):
    """
    An environment that manages everything necessary to expose telemetry
    capabilties.
    """

    def __init__(self, mtu: int, init_time: float = None,
                 metrics_rate: float = None,
                 initial_channels: List[Channel] = None,
                 initial_enums: List[UserEnum] = None) -> None:
        """ Construct a new telemetry environment. """

        super().__init__(mtu, initial_channels, metrics_rate, init_time)
        self.enum_registry = EnumRegistry(initial_enums)
        self.type_registry = get_default()
        assert self.enum_registry.add_enum(self.framer.get_types())[0]
        self.enum_registry.export(self.type_registry)
        self.enum_channel_types: Dict[int, int] = defaultdict(lambda: -1)
        if self.metrics is not None:
            self.add_metric("enum_count", Primitive.UINT32, True,
                            (self.enum_registry.count(), self.get_time()))
            self.add_metric("type_count", Primitive.UINT32, True,
                            (self.type_registry.count(), self.get_time()))

    def add_enum_channel(self, name: str, enum_name: str, rate: float,
                         track_change: bool = False,
                         initial: Tuple[str, Optional[float]] = None) -> int:
        """ Add a channel that stores an enumeration value."""

        new_chan = self.add_channel(name, ENUM_TYPE, rate, track_change)
        enum_type = self.enum_registry.get_id(enum_name)
        assert enum_type is not None
        self.enum_channel_types[new_chan] = enum_type
        if initial is not None:
            chan = self.channel_registry.get_item(new_chan)
            assert chan is not None
            enum_def = self.enum_registry.get_item(enum_type)
            assert enum_def is not None
            assert chan.set(enum_def.get_value(initial[0]), initial[1])
        return new_chan

    def add_enum_metric(self, name: str, enum_name: str,
                        track_change: bool = False,
                        initial: Tuple[str, Optional[float]] = None) -> None:
        """ Add a metric based on an enumeration definition. """

        if self.metrics is not None and not self.has_metric(name):
            self.metrics[name] = self.add_enum_channel(name, enum_name,
                                                       float(), track_change,
                                                       initial)
            self.set_metric_rate(name, self.get_metric("metrics_rate"))

    def set_enum_metric(self, name: str, data: str,
                        time: float = None) -> None:
        """ Set the value for an enumeration metric. """

        assert self.metrics is not None
        if name in self.metrics:
            chan = self.channel_registry.get_item(self.metrics[name])
            assert chan is not None
            enum_type = self.enum_channel_types[self.metrics[name]]
            enum_def = self.enum_registry.get_item(enum_type)
            assert enum_def is not None
            assert chan.set(enum_def.get_value(data), time)

    def get_enum_metric(self, name: str) -> str:
        """ Get the currently-held enum String of a metric channel by name. """

        assert self.metrics is not None
        enum_type = self.enum_channel_types[self.metrics[name]]
        enum_def = self.enum_registry.get_item(enum_type)
        assert enum_def is not None
        return enum_def.get_str(self.get_metric(name))

    def get_enum_value(self, chan_id: int) -> str:
        """ Get the String value currently held by an enum channel. """

        enum_type = self.enum_channel_types[chan_id]
        enum_def = self.enum_registry.get_item(enum_type)
        assert enum_def is not None
        return enum_def.get_str(self.get_value(chan_id))

    def set_enum_now(self, channel_id: int, data: str) -> None:
        """ Set an enum channel with the provided value, assign time. """

        enum_type = self.enum_channel_types[channel_id]
        enum_def = self.enum_registry.get_item(enum_type)
        assert enum_def is not None
        self.set_now(channel_id, enum_def.get_value(data))

    def add_from_enum(self, enum_class: Type[Enum]) -> int:
        """ Add an enumeration from an enum class. """

        return self.add_enum(from_enum(enum_class))

    def add_enum(self, enum: UserEnum) -> int:
        """ Add a user enumeration to this environment's management. """

        with self.lock:
            if self.enum_registry.get_enum(enum)[0]:
                return self.enum_registry.get_enum(enum)[1]
            result = self.enum_registry.add_enum(enum)
            assert result[0]
            assert self.enum_registry.export(self.type_registry)
            if self.metrics is not None:
                self.set_metric("enum_count", self.enum_registry.count())
                self.set_metric("type_count", self.type_registry.count())
        return result[1]
