
"""
vtelem - An interface for creating telemetered applications.
"""

# built-in
import socket
import threading
from typing import Tuple

# internal
from vtelem.mtu import discover_ipv4_mtu, DEFAULT_MTU
from vtelem.factories.daemon_manager import create_daemon_manager_commander
from vtelem.factories.telemetry_environment import create_channel_commander
from vtelem.factories.telemetry_server import register_http_handlers
from .channel_group_registry import ChannelGroupRegistry
from .command_queue_daemon import CommandQueueDaemon
from .daemon_base import DaemonOperation
from .daemon_manager import DaemonManager
from .http_daemon import HttpDaemon
from .http_request_mapper import MapperAwareRequestHandler
from .stream_writer import StreamWriter
from .telemetry_daemon import TelemetryDaemon
from .time_keeper import TimeKeeper
from .udp_client_manager import UdpClientManager


class TelemetryServer(HttpDaemon):
    """ A class for application-level telemetry integration. """

    def __init__(self, tick_length: float, telem_rate: float,
                 address: Tuple[str, int] = None,
                 metrics_rate: float = None,
                 app_id_basis: float = None) -> None:
        """
        Construct a new telemetry server that can be commanded over http.
        """

        self.daemons = DaemonManager()
        self.state_sem = threading.Semaphore(0)

        # add the ticker
        self.time_keeper = TimeKeeper("time", tick_length)
        assert self.daemons.add_daemon(self.time_keeper)

        # dynamically build mtu, take the minimum of the system's loopback
        # interface, or a practical mtu based on a 1500-byte Ethernet II frame
        # (we will re-evalute mtu when we connect new clients)
        mtu = discover_ipv4_mtu((socket.getfqdn(), 0)) - (60 + 8)
        telem = TelemetryDaemon("telemetry", mtu, telem_rate, self.time_keeper,
                                metrics_rate, app_id_basis=app_id_basis)
        telem.handle_new_mtu(DEFAULT_MTU)
        self.channel_groups = ChannelGroupRegistry(telem)
        assert self.daemons.add_daemon(telem)

        # add the telemetry-stream writer
        writer = StreamWriter("stream", telem.frame_queue)
        self.udp_clients = UdpClientManager(writer)
        assert self.daemons.add_daemon(writer)

        # add the http daemon
        super().__init__("http", address, MapperAwareRequestHandler, telem,
                         self.time_keeper)
        register_http_handlers(self, telem)

        # add the command-queue daemon
        queue_daemon = CommandQueueDaemon("command", telem, self.time_keeper)
        create_channel_commander(telem, queue_daemon)
        assert self.daemons.add_daemon(queue_daemon)

        # make the daemon-manager commandable
        create_daemon_manager_commander(self.daemons, queue_daemon)

    def scale_speed(self, scalar: float) -> None:
        """ Change the time scaling for the time keeper. """

        self.daemons.perform_all(DaemonOperation.PAUSE)
        self.time_keeper.scale(scalar)
        self.daemons.perform_all(DaemonOperation.UNPAUSE)

    def start_all(self) -> None:
        """ Start everything. """

        self.daemons.perform_all(DaemonOperation.START)
        self.start()
        with self.lock:
            self.state_sem.release()

    def stop_all(self) -> None:
        """ Stop everything. """

        self.daemons.perform_all(DaemonOperation.STOP)
        self.stop()
        self.close()
        with self.lock:
            self.state_sem.release()

    def await_shutdown(self, timeout: float = None) -> None:
        """
        Wait for startup, then shutdown of this server. Otherwise attempt a
        manual shutdown if this is interrupted.
        """

        try:
            self.state_sem.acquire()
            if not self.state_sem.acquire(True, timeout):  # type: ignore
                self.stop_all()
        except KeyboardInterrupt:
            self.stop_all()
