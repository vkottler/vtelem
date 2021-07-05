"""
vtelem - An interface for setting up and tearing down outgoing udp streams.
"""

# built-in
import logging
import socket
from typing import Dict, Tuple, Any

# internal
from vtelem.mtu import create_udp_socket, discover_mtu
from .stream_writer import StreamWriter
from .time_entity import LockEntity

LOG = logging.getLogger(__name__)


class UdpClientManager(LockEntity):
    """A class for managing outgoing udp streams."""

    def __init__(self, writer: StreamWriter) -> None:
        """
        Construct a new client manager, which will produce streams to the
        provided stream-writer.
        """

        super().__init__()
        self.writer = writer

        self.clients: Dict[int, Tuple[socket.SocketType, Any]] = {}
        self.stream_ids: Dict[int, int] = {}

        assert self.writer.error_handle is None

        def closer(stream_id: int) -> None:
            """
            Close a client socket, based on its stream-writer stream
            identifier.
            """

            with self.lock:
                sock, sock_file = self.clients[stream_id]
                del self.clients[stream_id]
            name = sock.getsockname()
            LOG.info("closing stream client '%s:%d'", name[0], name[1])
            try:
                sock_file.close()
            except ConnectionRefusedError:
                pass
            sock.close()

        self.closer = closer
        self.writer.error_handle = self.closer

    def client_name(self, sock_id: int) -> Tuple[str, int]:
        """Get the host and port of a client."""

        assert sock_id in self.clients
        return self.clients[sock_id][0].getsockname()

    def add_client(self, host: Tuple[str, int]) -> Tuple[int, int]:
        """Add a new client connection by hostname and port."""

        sock = create_udp_socket(host)
        mtu = discover_mtu(sock)
        mtu -= 60 + 8  # subtract ip and udp header space
        sock_file = sock.makefile("wb")
        sock_file.flush()
        with self.lock:
            sock_id = self.writer.add_stream(sock_file)
            self.clients[sock_id] = (sock, sock_file)
            name = sock.getsockname()
        LOG.info(
            "adding stream client '%s:%d' -> '%s:%d'",
            name[0],
            name[1],
            host[0],
            host[1],
        )
        return sock_id, mtu

    def remove_all(self) -> None:
        """Remove all active clients."""

        with self.lock:
            for sock_id in list(self.clients.keys()):
                self.remove_client(sock_id)

    def remove_client(self, sock_id: int) -> None:
        """Remove a client connection by integer identifier, closes it."""

        with self.lock:
            if self.writer.remove_stream(sock_id):
                self.closer(sock_id)
