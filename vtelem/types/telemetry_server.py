"""
vtelem - Common type definitions for the telemetry server.
"""

# built-in
from typing import Any, Callable, Dict

# internal
from vtelem.channel.group_registry import ChannelGroupRegistry

AppSetup = Callable[[ChannelGroupRegistry, Dict[str, Any]], None]
AppLoop = Callable[[ChannelGroupRegistry, Dict[str, Any]], None]
