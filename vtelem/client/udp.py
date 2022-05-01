"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         udp listener.
"""

# built-in
from contextlib import contextmanager
from queue import Queue
import socket
from typing import Iterator, Tuple

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.client.socket import SocketClient
from vtelem.mtu import (
    DEFAULT_MTU,
    Host,
    create_udp_socket,
    get_free_port,
    host_resolve_zero,
)
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

        host = host_resolve_zero(socket.SOCK_DGRAM, host)
        sock = create_udp_socket(host, False)

        def stop_server() -> None:
            """
            Close this listener by sending a final, zero-length payload to
            un-block recv, then closing the socket.
            """
            self.socket.sendto(bytearray(), self.socket.getsockname())

        super().__init__(
            sock,
            stop_server,
            output_stream,
            channel_registry,
            app_id,
            env,
            mtu,
        )

        def bind(curr_sock: socket.SocketType) -> socket.SocketType:
            """
            Re-bind a udp socket if the previously used one is now closed.
            """

            result = curr_sock
            if result.fileno() == -1:
                result = create_udp_socket(host, False)
            return result

        self.function["init"] = bind


@contextmanager
def create(
    manager: UdpClientManager,
    env: TelemetryEnvironment,
    test_port: int = 0,
    mtu: int = DEFAULT_MTU,
    local_addr: str = "0.0.0.0",
) -> Iterator[Tuple[UdpClient, Queue]]:
    """Create a udp client from a client manager and telemetry environment."""

    host = Host(
        local_addr, get_free_port(socket.SOCK_DGRAM, test_port=test_port)
    )
    queue = manager.writer.get_queue()
    client = UdpClient(host, queue, env.channel_registry, env.app_id, env, mtu)
    client_id, new_mtu = manager.add_client(host, True)
    client.update_mtu(new_mtu)
    try:
        yield client, queue
    finally:
        manager.remove_client(client_id)
