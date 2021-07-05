"""
vtelem - An interface for creating telemetered applications.
"""

# built-in
from collections import defaultdict
from contextlib import contextmanager
import socket
import threading
from typing import Any, Dict, Tuple, Iterator

# internal
from vtelem.mtu import discover_ipv4_mtu, DEFAULT_MTU
from vtelem.factories.daemon_manager import create_daemon_manager_commander
from vtelem.factories.telemetry_environment import create_channel_commander
from vtelem.factories.telemetry_server import register_http_handlers
from vtelem.factories.udp_client_manager import create_udp_client_commander
from vtelem.factories.websocket_daemon import commandable_websocket_daemon
from vtelem.types.telemetry_server import AppSetup, AppLoop
from .channel_group_registry import ChannelGroupRegistry
from .command_queue_daemon import CommandQueueDaemon
from .daemon import Daemon
from .daemon_base import DaemonOperation
from .daemon_manager import DaemonManager
from .http_daemon import HttpDaemon
from .http_request_mapper import MapperAwareRequestHandler
from .service_registry import ServiceRegistry
from .stream_writer import StreamWriter
from .telemetry_daemon import TelemetryDaemon
from .time_keeper import TimeKeeper
from .udp_client_manager import UdpClientManager
from .websocket_telemetry_daemon import WebsocketTelemetryDaemon


class TelemetryServer(HttpDaemon):
    """A class for application-level telemetry integration."""

    def __init__(
        self,
        tick_length: float,
        telem_rate: float,
        http_address: Tuple[str, int] = None,
        metrics_rate: float = None,
        app_id_basis: float = None,
        websocket_cmd_address: Tuple[str, int] = None,
        websocket_tlm_address: Tuple[str, int] = None,
    ) -> None:
        """
        Construct a new telemetry server that can be commanded over http.
        """

        self.daemons = DaemonManager()
        self.state_sem = threading.Semaphore(0)
        self.first_start = True

        # add the ticker
        self.time_keeper = TimeKeeper("time", tick_length)
        assert self.daemons.add_daemon(self.time_keeper)

        # dynamically build mtu, take the minimum of the system's loopback
        # interface, or a practical mtu based on a 1500-byte Ethernet II frame
        # (we will re-evalute mtu when we connect new clients)
        mtu = discover_ipv4_mtu((socket.getfqdn(), 0)) - (60 + 8)
        telem = TelemetryDaemon(
            "telemetry",
            mtu,
            telem_rate,
            self.time_keeper,
            metrics_rate,
            app_id_basis=app_id_basis,
        )
        telem.handle_new_mtu(DEFAULT_MTU)
        self.channel_groups = ChannelGroupRegistry(telem)
        telem.registries["channel_groups"] = self.channel_groups
        telem.registries["services"] = ServiceRegistry()
        assert self.daemons.add_daemon(telem)

        # add the telemetry-stream writer
        writer = StreamWriter("stream", telem.frame_queue)
        self.udp_clients = UdpClientManager(writer)
        assert self.daemons.add_daemon(writer)

        # add the websocket-telemetry daemon
        assert self.daemons.add_daemon(
            WebsocketTelemetryDaemon(
                "websocket_telemetry",
                writer,
                websocket_tlm_address,
                telem,
                self.time_keeper,
            )
        )

        # add the http daemon
        super().__init__(
            "http",
            http_address,
            MapperAwareRequestHandler,
            telem,
            self.time_keeper,
        )

        # add the command-queue daemon
        queue_daemon = CommandQueueDaemon("command", telem, self.time_keeper)
        create_channel_commander(telem, queue_daemon)
        assert self.daemons.add_daemon(queue_daemon)
        register_http_handlers(self, telem, queue_daemon)

        # add the websocket-command daemon
        ws_cmd = commandable_websocket_daemon(
            "websocket_command",
            queue_daemon,
            websocket_cmd_address,
            telem,
            self.time_keeper,
        )
        assert self.daemons.add_daemon(ws_cmd, ["stream"])

        # make the daemon-manager commandable
        create_daemon_manager_commander(self.daemons, queue_daemon)

        # make the udp-client-manager commandable
        create_udp_client_commander(self.udp_clients, queue_daemon)

    def register_application(
        self, name: str, rate: float, setup: AppSetup, loop: AppLoop
    ) -> bool:
        """Attempt to register a new application thread."""

        app_data: Dict[str, Any] = defaultdict(lambda: None)

        def setup_caller(*_, **__) -> None:
            """Call the application's setup with the expected arguments."""
            setup(self.channel_groups, app_data)

        def loop_caller(*_, **__) -> None:
            """Call the application's loop with the expected arguments."""
            loop(self.channel_groups, app_data)

        telem = self.daemons.get("telemetry")
        assert isinstance(telem, TelemetryDaemon)
        daemon = Daemon(
            name,
            loop_caller,
            rate,
            env=telem,
            time_keeper=self.time_keeper,
            init=setup_caller,
        )
        result = self.daemons.add_daemon(daemon, ["telemetry"])
        if not self.first_start:
            app_daemon = self.daemons.get(name)
            assert app_daemon is not None
            assert app_daemon.perform(DaemonOperation.START)
        return result

    def scale_speed(self, scalar: float) -> None:
        """Change the time scaling for the time keeper."""

        self.daemons.perform_all(DaemonOperation.PAUSE)
        self.time_keeper.scale(scalar)
        self.daemons.perform_all(DaemonOperation.UNPAUSE)

    def start_all(self) -> None:
        """Start everything."""

        telem = self.daemons.get("telemetry")
        assert isinstance(telem, TelemetryDaemon)
        kwargs: dict = {"service_registry": telem.registries["services"]}
        kwargs["first_start"] = self.first_start
        self.daemons.perform_all(DaemonOperation.START, **kwargs)
        self.start(**kwargs)
        self.first_start = False

        with self.lock:
            self.state_sem.release()

    def stop_all(self) -> None:
        """Stop everything."""

        self.daemons.perform_all(DaemonOperation.STOP)
        self.stop()
        self.close()
        self.udp_clients.remove_all()
        with self.lock:
            self.state_sem.release()

    @contextmanager
    def booted(self, *_, **__) -> Iterator[None]:
        """
        Provide a context manager that yields when this daemon is running and
        automatically stops it.
        """

        try:
            self.start_all()
            yield
        finally:
            self.stop_all()

    def await_shutdown(self, timeout: float = None) -> None:
        """
        Wait for startup, then shutdown of this server. Otherwise attempt a
        manual shutdown if this is interrupted.
        """

        try:
            # pylint:disable=consider-using-with
            self.state_sem.acquire()
            if not self.state_sem.acquire(True, timeout):  # type: ignore
                self.stop_all()
        except KeyboardInterrupt:
            self.stop_all()
