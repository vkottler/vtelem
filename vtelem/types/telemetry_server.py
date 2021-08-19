"""
vtelem - Common type definitions for the telemetry server.
"""

# built-in
from typing import Any, Callable, Dict, List, NamedTuple, Optional

# internal
from vtelem.channel.group_registry import ChannelGroupRegistry
from vtelem.mtu import Host

AppSetup = Callable[[ChannelGroupRegistry, Dict[str, Any]], None]
AppLoop = Callable[[ChannelGroupRegistry, Dict[str, Any]], None]


class TelemetryServices(NamedTuple):
    """
    A container for all possible telemetry services that can be configured.
    """

    http: Optional[Host] = None
    websocket_cmd: Optional[Host] = None
    websocket_tlm: Optional[Host] = None
    tcp: Optional[Host] = None
    udp: Optional[List[Host]] = None
