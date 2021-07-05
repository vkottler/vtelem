"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         udp listener.
"""

# built-in
import logging
from queue import Queue
from typing import Tuple

# internal
from vtelem.mtu import create_udp_socket, DEFAULT_MTU
from .daemon_base import DaemonBase, DaemonState
from .telemetry_environment import TelemetryEnvironment
from .type_primitive import TypePrimitive

LOG = logging.getLogger(__name__)


class TelemetryProxy(DaemonBase):
    """
    A class for publishing decoded telemetry frames into a queue as a daemon.
    """

    def __init__(
        self,
        host: Tuple[str, int],
        output_stream: Queue,
        app_id: TypePrimitive,
        env: TelemetryEnvironment,
        mtu: int = DEFAULT_MTU,
    ) -> None:
        """Construct a new telemetry proxy."""

        self.socket = create_udp_socket(host, False)
        self.mtu = mtu
        name = self.socket.getsockname()
        super().__init__("{}:{}".format(name[0], name[1]), env)
        self.frames = output_stream
        self.expected_id = app_id
        self.curr_id = TypePrimitive(self.expected_id.type)

        def stop_server() -> None:
            """
            Close this listener by sending a final, zero-length payload to
            un-block recv, then closing the socket.
            """
            LOG.info("%s: closing udp listener", self.name)
            self.socket.sendto(bytearray(), self.socket.getsockname())
            self.socket.close()
            self.frames.put(None)

        self.function["inject_stop"] = stop_server

    def update_mtu(self, new_mtu: int) -> None:
        """
        Update this proxy's understanding of the maximum transmission-unit
        size.
        """

        with self.lock:
            self.mtu = new_mtu
        LOG.info("%s: mtu set to %d", self.name, new_mtu)

    def run(self, *_, **__) -> None:
        """Read from the listener and enqueue decoded frames."""

        errored = False
        while self.state != DaemonState.STOPPING and not errored:
            with self.lock:
                mtu = self.mtu
            try:
                data = self.socket.recv(mtu)
                if not data:
                    continue
            except OSError as exc:
                LOG.error(exc)
                errored = True
                continue

            assert self.env is not None
            self.frames.put(
                self.env.decode_frame(data, len(data), self.expected_id)
            )
