"""
vtelem - An interface for managing telemetry-serving tcp servers.
"""

# built-in
import logging
import socketserver
from threading import Semaphore
from typing import Any, Dict, Tuple

# internal
from .daemon_base import DaemonBase
from .stream_writer import StreamWriter, QueueClientManager
from .telemetry_environment import TelemetryEnvironment

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

        sem = Semaphore(0)

        def closer() -> None:
            """Increment the semaphore, signaling connection close."""
            sem.release()

        daemon: TcpTelemetryDaemon = self.server.daemon  # type: ignore
        writer: StreamWriter = daemon.writer
        self.wfile.name = "tcp://{}:{}".format(  # type: ignore
            self.client_address[0], self.client_address[1]
        )
        with daemon.lock:
            stream_id = writer.add_stream(self.wfile, closer)  # type: ignore
            daemon.client_sems[stream_id] = sem
        try:
            sem.acquire()  # pylint:disable=consider-using-with
        finally:
            writer.remove_stream(stream_id, False)
            LOG.info(
                "%s:%d disconnected",
                self.client_address[0],
                self.client_address[1],
            )


class TcpTelemetryDaemon(QueueClientManager, DaemonBase):
    """A class for serving telemetry frames to tcp clients."""

    def __init__(
        self,
        name: str,
        writer: StreamWriter,
        env: TelemetryEnvironment,
        address: Tuple[str, int] = ("0.0.0.0", 0),
        time_keeper: Any = None,
    ) -> None:
        """Construct a new tcp telemetry daemon."""

        QueueClientManager.__init__(self, name, writer)
        DaemonBase.__init__(self, name, env, time_keeper)

        self.server = socketserver.ThreadingTCPServer(
            address, TcpTelemetryHandler
        )
        self.client_sems: Dict[int, Semaphore] = {}

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

    @property
    def address(self) -> Tuple[str, int]:
        """Get this server's bound address."""

        return self.server.server_address

    def run(self, *_, **__) -> None:
        """Listen for client connections."""

        self.server.serve_forever(0.1)
