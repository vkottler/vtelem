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


class Service(NamedTuple):
    """A definition for a network service."""

    name: str
    host: Optional[Host] = None
    enabled: bool = True


class TelemetryServices(NamedTuple):
    """
    A container for all possible telemetry services that can be configured.
    """

    http: Service
    websocket_cmd: Service
    websocket_tlm: Service
    tcp_tlm: Service
    udp: Optional[List[Host]] = None


def default_services(**kwargs: Service) -> TelemetryServices:
    """Create a default set of service definitions."""

    return TelemetryServices(
        kwargs.get("http", Service("http")),
        kwargs.get("websocket_command", Service("websocket_command")),
        kwargs.get("websocket_telemetry", Service("websocket_telemetry")),
        kwargs.get("tcp_telemetry", Service("tcp_telemetry")),
    )
