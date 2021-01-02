
"""
vtelem - An interface for creating telemetered applications.
"""

# built-in
from http.server import SimpleHTTPRequestHandler
import socket
from typing import Tuple

# internal
from vtelem.mtu import discover_ipv4_mtu, DEFAULT_MTU
from .channel_group_registry import ChannelGroupRegistry
from .daemon_base import DaemonOperation
from .daemon_manager import DaemonManager
from .http_daemon import HttpDaemon
from .stream_writer import StreamWriter
from .telemetry_daemon import TelemetryDaemon
from .time_keeper import TimeKeeper
from .udp_client_manager import UdpClientManager


class TelemetryServer(HttpDaemon):
    """ A class for application-level telemetry integration. """

    def __init__(self, tick_length: float, telem_rate: float,
                 address: Tuple[str, int] = None,
                 metrics_rate: float = None) -> None:
        """
        Construct a new telemetry server that can be commanded over http.
        """

        self.daemons = DaemonManager()

        # add the ticker
        self.time_keeper = TimeKeeper("time", tick_length)
        assert self.daemons.add_daemon(self.time_keeper)

        # dynamically build mtu, take the minimum of the system's loopback
        # interface, or a practical mtu based on a 1500-byte Ethernet II frame
        # (we will re-evalute mtu when we connect new clients)
        telem = TelemetryDaemon("telemetry",
                                discover_ipv4_mtu((socket.getfqdn(), 0)) - 8,
                                telem_rate, self.time_keeper, metrics_rate)
        telem.handle_new_mtu(DEFAULT_MTU)
        self.channel_groups = ChannelGroupRegistry(telem)
        assert self.daemons.add_daemon(telem)

        # add the telemetry-stream writer
        writer = StreamWriter("stream", telem.frame_queue)
        self.udp_clients = UdpClientManager(writer)
        assert self.daemons.add_daemon(writer)

        # add the http daemon
        super().__init__("http", address, SimpleHTTPRequestHandler, telem,
                         self.time_keeper)

    def scale_speed(self, scalar: float) -> None:
        """ Change the time scaling for the time keeper. """

        assert self.daemons.perform_all(DaemonOperation.PAUSE)
        self.time_keeper.scale(scalar)
        assert self.daemons.perform_all(DaemonOperation.UNPAUSE)
