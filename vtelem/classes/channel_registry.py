"""
vtelem - A module for managing channel registrations.
"""

# built-in
from typing import List, Tuple

# internal
from vtelem.enums.primitive import Primitive
from .channel import Channel, ChannelEncoder
from .registry import Registry


class ChannelRegistry(Registry[Channel]):
    """
    A class for managing channel-to-integer mappings so channel data can be
    transported efficiently over a wire-level protocol.
    """

    def __init__(self, initial_channels: List[Channel] = None) -> None:
        """Construct a new channel registry."""

        super().__init__("channels", None)
        if initial_channels is not None:
            for channel in initial_channels:
                self.add_channel(channel)

    def get_channel_type(self, chan_id: int) -> Primitive:
        """Get a channel's primitive type by its integer identifier."""

        channel = self.get_item(chan_id)
        assert channel is not None
        return channel.type

    def add_channel(self, channel: Channel) -> Tuple[bool, int]:
        """Attempt to register a channel."""

        return self.add(channel.name, channel)

    def describe(self, indented: bool = False) -> str:
        """Obtain a JSON String of the channel registry's current state."""

        return self.describe_raw(indented, ChannelEncoder)
