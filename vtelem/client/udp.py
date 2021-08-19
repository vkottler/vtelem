"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         udp listener.
"""

# built-in
from queue import Queue

# internal
from vtelem.client.socket import SocketClient
from vtelem.mtu import create_udp_socket, DEFAULT_MTU, Host
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.telemetry.environment import TelemetryEnvironment


class UdpClient(SocketClient):
    """
    A class for publishing decoded telemetry frames into a queue as a daemon,
    from a udp socket.
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
        """Construct a new udp client."""

        socket = create_udp_socket(host, False)

        def stop_server() -> None:
            """
            Close this listener by sending a final, zero-length payload to
            un-block recv, then closing the socket.
            """
            socket.sendto(bytearray(), socket.getsockname())

        super().__init__(
            socket,
            stop_server,
            output_stream,
            channel_registry,
            app_id,
            env,
            mtu,
        )
