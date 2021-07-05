"""
vtelem - Simplify management of logical groups of channels and synchronize
         their reading and writing.
"""

# built-in
from contextlib import contextmanager
from typing import Any, Dict, Iterator

# internal
from vtelem.enums.primitive import Primitive, default_val
from .telemetry_environment import TelemetryEnvironment


class ChannelGroup:
    """
    A class for managing groups of channels with atomic syncs to the
    environment.
    """

    def __init__(self, name: str, env: TelemetryEnvironment) -> None:
        """Construct a new channel group."""

        self.env = env
        self.name = name
        self.channels: Dict[str, Dict[str, Any]] = {}

    def add_channel(
        self,
        name: str,
        instance: Primitive,
        rate: float,
        track_change: bool = False,
    ) -> bool:
        """
        Attempt to add a channel to the environment and this group manager.
        """

        # the environment should catch duplicate channel names for us
        try:
            val = default_val(instance)
            real_name = "{}.{}".format(self.name, name)
            chan_id = self.env.add_channel(
                real_name,
                instance,
                rate,
                track_change,
                (val, self.env.get_time()),
            )
        except AssertionError:
            return False

        self.channels[name] = {"id": chan_id, "value": val, "is_enum": False}
        return True

    def add_enum_channel(
        self,
        name: str,
        enum_name: str,
        rate: float,
        track_change: bool = False,
    ) -> bool:
        """
        Attempt to add an enum channel to the environment and this group
        manager.
        """

        # make sure the enum is registered
        enum_id = self.env.enum_registry.get_id(enum_name)
        if enum_id is None:
            return False

        # get the default enum value
        enum = self.env.enum_registry.get_item(enum_id)
        assert enum is not None
        val = enum.default()

        # the environment should catch duplicate channel names for us
        try:
            real_name = "{}.{}".format(self.name, name)
            chan_id = self.env.add_enum_channel(
                real_name,
                enum_name,
                rate,
                track_change,
                (val, self.env.get_time()),
            )
        except AssertionError:
            return False

        self.channels[name] = {"id": chan_id, "is_enum": True}
        return True

    @contextmanager
    def data(self) -> Iterator[Dict[str, Any]]:
        """
        Provide channel data in a context manager so it can be automatically
        synced with the environment.
        """

        try:
            data = self.read()
            yield data
        finally:
            self.write(data)

    def read(self) -> Dict[str, Any]:
        """Read all channel values from the environment, atomically."""

        values = {}
        with self.env.lock:
            for name, channel in self.channels.items():
                if channel["is_enum"]:
                    values[name] = self.env.get_enum_value(channel["id"])
                else:
                    values[name] = self.env.get_value(channel["id"])
        return values

    def write(self, values: Dict[str, Any]) -> None:
        """Write the values into the environment."""

        with self.env.lock:
            for name, value in values.items():
                assert name in self.channels
                chan = self.channels[name]
                if chan["is_enum"]:
                    self.env.set_enum_now(chan["id"], value)
                else:
                    self.env.set_now(chan["id"], value)
