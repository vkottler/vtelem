"""
vtelem - An interface for managing telemetry-serving tcp servers.
"""

# built-in
import socketserver
from typing import Any, Tuple

# internal
from .daemon_base import DaemonBase
from .stream_writer import StreamWriter, QueueClientManager
from .telemetry_environment import TelemetryEnvironment


class TcpTelemetryHandler(socketserver.StreamRequestHandler):
    """A stream-request handler for serving telemetry frames to clients."""

    def handle(self) -> None:
        """
        Send frames to the connected client until they close the connection,
        or we're otherwise signaled to shutdown.
        """

        # need to grab frames from the environment, but we need to figure out
        # how to not deplete the queue for other clients, tricky


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
        self.function["inject_stop"] = self.server.shutdown
        self.server.env = env  # type: ignore

    @property
    def address(self) -> Tuple[str, int]:
        """Get this server's bound address."""

        return self.server.server_address

    def run(self, *_, **__) -> None:
        """Listen for client connections."""

        self.server.serve_forever(0.1)
