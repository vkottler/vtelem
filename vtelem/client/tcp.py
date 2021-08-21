"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         tcp listener.
"""

# built-in
import socket
from queue import Queue

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.client.socket import SocketClient
from vtelem.mtu import DEFAULT_MTU, Host
from vtelem.telemetry.environment import TelemetryEnvironment


class TcpClient(SocketClient):
    """
    A class for publishing decoded telemetry frames into a queue as a daemon,
    from a tcp socket.
    """

    def __init__(
        self,
        host: Host,
        output_stream: Queue,
        channel_registry: ChannelRegistry,
        app_id: TypePrimitive = None,
        env: TelemetryEnvironment = None,
        mtu: int = DEFAULT_MTU,
    ) -> None:
        """Construct a new tcp client."""

        sock = socket.create_connection(host)
        sock.settimeout(0.1)

        def stop_server() -> None:
            """Nothing special needed to close this connection."""

            sock.shutdown(socket.SHUT_RD)

        super().__init__(
            sock,
            stop_server,
            output_stream,
            channel_registry,
            app_id,
            env,
            mtu,
        )
