
"""
vtelem - TODO.
"""

# built-in
import logging
import socket
from typing import Dict, Tuple, Any

# internal
from vtelem.mtu import create_udp_socket, discover_mtu
from .stream_writer import StreamWriter

LOG = logging.getLogger(__name__)


class UdpClientManager:
    """ TODO """

    def __init__(self, writer: StreamWriter) -> None:
        """ TODO """

        self.writer = writer

        self.clients: Dict[int, Tuple[socket.SocketType, Any]] = {}
        self.stream_ids: Dict[int, int] = {}

        assert self.writer.error_handle is None

        def closer(stream_id: int) -> None:
            """
            Close a client socket, based on its stream-writer stream
            identifier.
            """

            sock, sock_file = self.clients[stream_id]
            name = sock.getsockname()
            LOG.info("closing stream client '%s:%d'", name[0], name[1])
            sock_file.close()
            sock.close()
            del self.clients[stream_id]

        self.closer = closer
        self.writer.error_handle = self.closer

    def add_client(self, host: Tuple[str, int]) -> Tuple[int, int]:
        """ Add a new client connection by hostname and port. """

        sock = create_udp_socket(host)
        mtu = discover_mtu(sock)
        sock_file = sock.makefile("wb")
        sock_id = self.writer.add_stream(sock_file)
        self.clients[sock_id] = (sock, sock_file)
        name = sock.getsockname()
        LOG.info("adding stream client '%s:%d'", name[0], name[1])
        return sock_id, mtu

    def remove_client(self, sock_id: int) -> None:
        """ Remove a client connection by integer identifier, closes it. """

        if self.writer.remove_stream(sock_id):
            self.closer(sock_id)
