"""
vtelem - An interface for creating telemetered applications.
"""

# built-in
from collections import defaultdict
from contextlib import contextmanager
import socket
import threading
from typing import Any, Dict, Iterator

# internal
from vtelem.channel.group_registry import ChannelGroupRegistry
from vtelem.classes.http_request_mapper import MapperAwareRequestHandler
from vtelem.classes.time_keeper import TimeKeeper
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.daemon import DaemonOperation
from vtelem.daemon.command_queue import CommandQueueDaemon
from vtelem.daemon.http import HttpDaemon
from vtelem.daemon.manager import DaemonManager
from vtelem.daemon.synchronous import Daemon
from vtelem.daemon.tcp_telemetry import TcpTelemetryDaemon
from vtelem.daemon.telemetry import TelemetryDaemon
from vtelem.daemon.websocket_telemetry import WebsocketTelemetryDaemon
from vtelem.factories.daemon_manager import create_daemon_manager_commander
from vtelem.factories.telemetry_environment import create_channel_commander
from vtelem.factories.telemetry_server import register_http_handlers
from vtelem.factories.udp_client_manager import create_udp_client_commander
from vtelem.factories.websocket_daemon import commandable_websocket_daemon
from vtelem.mtu import DEFAULT_MTU, Host, discover_ipv4_mtu, mtu_to_usable
from vtelem.registry.service import ServiceRegistry
from vtelem.stream.writer import StreamWriter
from vtelem.types.telemetry_server import (
    AppLoop,
    AppSetup,
    TelemetryServices,
    default_services,
)


class TelemetryServer(HttpDaemon):
    """A class for application-level telemetry integration."""

    def __init__(
        self,
        tick_length: float,
        telem_rate: float,
        metrics_rate: float = None,
        app_id_basis: float = None,
        services: TelemetryServices = None,
    ) -> None:
        """
        Construct a new telemetry server that can be commanded over http.
        """

        if services is None:
            services = default_services()

        self.daemons = DaemonManager()
        self.state_sem = threading.Semaphore(0)
        self.first_start = True

        # add the ticker
        self.time_keeper = TimeKeeper("time", tick_length)
        assert self.daemons.add_daemon(self.time_keeper)

        # dynamically build mtu, take the minimum of the system's loopback
        # interface, or a practical mtu based on a 1500-byte Ethernet II frame
        # (we will re-evalute mtu when we connect new clients)
        mtu = mtu_to_usable(discover_ipv4_mtu(Host(socket.getfqdn(), 0)))
        telem = TelemetryDaemon(
            "telemetry",
            mtu,
            telem_rate,
            self.time_keeper,
            metrics_rate,
            app_id_basis=app_id_basis,
            use_crc=False,
        )
        telem.handle_new_mtu(DEFAULT_MTU)
        self.channel_groups = ChannelGroupRegistry(telem)
        telem.registries["channel_groups"] = self.channel_groups
        telem.registries["services"] = ServiceRegistry()
        assert self.daemons.add_daemon(telem)

        # add the telemetry-stream writer
        writer = StreamWriter(
            "stream",
            telem.frame_queue,
            None,
            telem,
            self.time_keeper,
        )
        self.udp_clients = UdpClientManager(writer)
        assert self.daemons.add_daemon(writer)

        # add the websocket-telemetry daemon
        if services.websocket_tlm.enabled:
            assert self.daemons.add_daemon(
                WebsocketTelemetryDaemon(
                    services.websocket_tlm.name,
                    writer,
                    services.websocket_tlm.host,
                    telem,
                    self.time_keeper,
                )
            )

        # add the tcp-telemetry daemon
        if services.tcp_tlm.enabled:
            assert self.daemons.add_daemon(
                TcpTelemetryDaemon(
                    services.tcp_tlm.name,
                    writer,
                    telem,
                    services.tcp_tlm.host,
                    self.time_keeper,
                )
            )

        # add the http daemon
        super().__init__(
            services.http.name,
            services.http.host,
            MapperAwareRequestHandler,
            telem,
            self.time_keeper,
        )
        self.http_enabled = services.http.enabled

        # add the command-queue daemon
        queue_daemon = CommandQueueDaemon("command", telem, self.time_keeper)
        create_channel_commander(telem, queue_daemon)
        assert self.daemons.add_daemon(queue_daemon)
        register_http_handlers(self, telem, queue_daemon)

        # add the websocket-command daemon
        if services.websocket_cmd.enabled:
            ws_cmd = commandable_websocket_daemon(
                services.websocket_cmd.name,
                queue_daemon,
                services.websocket_cmd.host,
                telem,
                self.time_keeper,
            )
        assert self.daemons.add_daemon(ws_cmd, ["stream"])

        # make the daemon-manager commandable
        create_daemon_manager_commander(self.daemons, queue_daemon)

        # make the udp-client-manager commandable
        create_udp_client_commander(self.udp_clients, queue_daemon)

        # add initial udp clients
        self.udp_clients.add_clients(
            services.udp if services.udp is not None else []
        )

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

        assert self.daemons.perform_all(DaemonOperation.PAUSE)
        self.time_keeper.scale(scalar)
        assert self.daemons.perform_all(DaemonOperation.UNPAUSE)

    def start_all(self) -> None:
        """Start everything."""

        telem = self.daemons.get("telemetry")
        assert isinstance(telem, TelemetryDaemon)
        kwargs: dict = {"service_registry": telem.registries["services"]}
        kwargs["first_start"] = self.first_start
        assert self.daemons.perform_all(DaemonOperation.START, **kwargs)

        if self.http_enabled:
            assert self.perform(DaemonOperation.START, **kwargs)
        self.first_start = False

        with self.lock:
            self.state_sem.release()

    def stop_all(self) -> None:
        """Stop everything."""

        assert self.daemons.perform_all(DaemonOperation.STOP)

        if self.http_enabled:
            assert self.perform(DaemonOperation.STOP)
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
            self.state_sem.acquire()
            yield
        finally:
            self.stop_all()
            self.state_sem.acquire()

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
        except KeyboardInterrupt:  # pragma: no cover
            self.stop_all()
