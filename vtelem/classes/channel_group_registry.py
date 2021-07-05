"""
vtelem - Allows channel groups to be managed by a single entity.
"""

# built-in
from contextlib import contextmanager
from typing import Dict, Iterator, Any

# internal
from vtelem.enums.primitive import Primitive
from .channel_group import ChannelGroup
from .registry import Registry
from .telemetry_environment import TelemetryEnvironment


class ChannelGroupRegistry(Registry[ChannelGroup]):
    """A class for managing an arbitrary number of channel groups."""

    def __init__(self, env: TelemetryEnvironment) -> None:
        """Construct a new group registry."""

        super().__init__("channel_groups")
        self.env = env

    def create_group(self, name: str) -> int:
        """Add a new, named channel group."""

        assert self.get_id(name) is None
        result = self.add(name, ChannelGroup(name, self.env))
        assert result[0]
        return result[1]

    def add_channel(
        self,
        group: int,
        name: str,
        instance: Primitive,
        rate: float,
        track_change: bool = False,
    ) -> None:
        """Add a channel to this named group."""

        group_inst = self.get_item(group)
        assert group_inst is not None
        group_inst.add_channel(name, instance, rate, track_change)

    def add_enum_channel(
        self,
        group: int,
        name: str,
        enum_name: str,
        rate: float,
        track_change: bool = False,
    ) -> None:
        """Add an enum channel to this named group."""

        group_inst = self.get_item(group)
        assert group_inst is not None
        group_inst.add_enum_channel(name, enum_name, rate, track_change)

    @contextmanager
    def group(self, group: int) -> Iterator[Dict[str, Any]]:
        """Yield the requested group's data."""

        group_inst = self.get_item(group)
        assert group_inst is not None
        with group_inst.data() as group_data:
            yield group_data
