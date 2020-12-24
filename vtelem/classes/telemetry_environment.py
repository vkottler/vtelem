
"""
vtelem - An environment that supports management of telemetry.
"""

# built-in
from collections import defaultdict
from enum import Enum
from typing import Any, List, Dict, Type

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

        super().__init__(mtu, initial_channels, metrics_rate)
        self.time: float = init_time if init_time is not None else float()
        self.enum_registry = EnumRegistry(initial_enums)
        self.type_registry = get_default()
        assert self.enum_registry.add_enum(self.framer.get_types())[0]
        self.enum_registry.export(self.type_registry)
        self.enum_channel_types: Dict[int, int] = defaultdict(lambda: -1)
        if self.metrics is not None:
            self.add_metric("enum_count", Primitive.UINT32, True,
                            (self.enum_registry.count(), init_time))
            self.add_metric("type_count", Primitive.UINT32, True,
                            (self.type_registry.count(), init_time))

    def add_enum_channel(self, name: str, enum_name: str, rate: float,
                         track_change: bool = False) -> int:
        """ Add a channel that stores an enumeration value."""

        new_chan = self.add_channel(name, ENUM_TYPE, rate, track_change)
        enum_type = self.enum_registry.get_id(enum_name)
        assert enum_type is not None
        self.enum_channel_types[new_chan] = enum_type
        return new_chan

    def set_enum_now(self, channel_id: int, data: str) -> None:
        """ Set an enum channel with the provided value, assign time. """

        enum_type = self.enum_channel_types[channel_id]
        enum_def = self.enum_registry.get_item(enum_type)
        assert enum_def is not None
        self.set_now(channel_id, enum_def.get_value(data))

    def set_now(self, channel_id: int, data: Any) -> None:
        """ set a channel with the provided value, assign time. """

        chan = self.channel_registry.get_item(channel_id)
        assert chan is not None
        assert chan.set(data, self.time)

    def advance_time(self, amount: float) -> None:
        """ Advance environment-time by a specified amount. """

        with self.lock:
            self.time += amount

    def add_from_enum(self, enum_class: Type[Enum]) -> int:
        """ Add an enumeration from an enum class. """

        return self.add_enum(from_enum(enum_class))

    def add_enum(self, enum: UserEnum) -> int:
        """ Add a user enumeration to this environment's management. """

        with self.lock:
            result = self.enum_registry.add_enum(enum)
            assert result[0]
            assert self.enum_registry.export(self.type_registry)
            if self.metrics is not None:
                self.set_metric("enum_count", self.enum_registry.count())
                self.set_metric("type_count", self.type_registry.count())
        return result[1]

    def dispatch_now(self, should_log: bool = True) -> int:
        """ Dispatch telemetry at the current time. """

        return self.dispatch(self.time, should_log)
