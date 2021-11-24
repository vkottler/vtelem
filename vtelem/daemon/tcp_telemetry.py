"""
vtelem - An interface for managing telemetry-serving tcp servers.
"""

# built-in
from io import BytesIO
import logging
from queue import Queue
import socketserver
from threading import Semaphore
from typing import Any, Dict, Tuple

# internal
from vtelem.client.tcp import TcpClient
from vtelem.daemon import DaemonBase
from vtelem.mtu import DEFAULT_MTU, Host
from vtelem.stream.writer import QueueClientManager, StreamWriter
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class TcpTelemetryHandler(socketserver.StreamRequestHandler):
    """A stream-request handler for serving telemetry frames to clients."""

    def handle(self) -> None:
        """
        Send frames to the connected client until they close the connection,
        or we're otherwise signaled to shutdown.
        """

        LOG.info(
            "%s:%d connected", self.client_address[0], self.client_address[1]
        )

        daemon: TcpTelemetryDaemon = self.server.daemon  # type: ignore
        daemon.increment_metric("clients")

        # make sure our stream has a name attribute
        stream: BytesIO = self.wfile  # type: ignore
        stream.name = f"{self.client_address[0]}:{self.client_address[1]}"

        # add the socket to the stream writer
        writer: StreamWriter = daemon.writer
        with daemon.lock:
            stream_id, sem = writer.add_semaphore_stream(stream)
            daemon.client_sems[stream_id] = sem

        # wait for something to signal us to close the connection
        try:
            sem.acquire()  # pylint:disable=consider-using-with
        finally:
            writer.remove_stream(stream_id, False)
            LOG.info(
                "%s:%d disconnected",
                self.client_address[0],
                self.client_address[1],
            )
            daemon.decrement_metric("clients")


class TcpTelemetryDaemon(QueueClientManager, DaemonBase):
    """A class for serving telemetry frames to tcp clients."""

    def __init__(
        self,
        name: str,
        writer: StreamWriter,
        env: TelemetryEnvironment,
        address: Host = None,
        time_keeper: Any = None,
    ) -> None:
        """Construct a new tcp telemetry daemon."""

        if address is None:
            address = Host()

        QueueClientManager.__init__(self, name, writer)
        DaemonBase.__init__(self, name, env, time_keeper)

        self.server = socketserver.ThreadingTCPServer(
            address, TcpTelemetryHandler
        )
        self.client_sems: Dict[int, Semaphore] = {}
        self.reset_metric("clients")

        def stopper() -> None:
            """Stop running this server and close active client connections."""

            self.server.shutdown()
            with self.lock:
                closed_clients = list(self.client_sems.keys())
            for client in closed_clients:
                self.client_sems[client].release()
                del self.client_sems[client]

        self.function["inject_stop"] = stopper
        self.server.daemon = self  # type: ignore

    def client(self, mtu: int = DEFAULT_MTU) -> Tuple[TcpClient, Queue]:
        """Create a client and output queue for this server."""

        assert self.env is not None
        queue = self.writer.get_queue()
        return (
            TcpClient(
                Host(*self.address),
                queue,
                self.env.channel_registry,
                self.env.app_id,
                self.env,
                mtu,
            ),
            queue,
        )

    @property
    def address(self) -> Tuple[str, int]:
        """Get this server's bound address."""

        return self.server.server_address

    def run(self, *_, **__) -> None:
        """Listen for client connections."""

        self.server.serve_forever(0.1)
