"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         socket.
"""

# built-in
import logging
from queue import Queue
from socket import SocketType
from typing import Callable

# internal
from vtelem.mtu import DEFAULT_MTU
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.daemon import DaemonBase, DaemonState
from vtelem.parsing.encapsulation import decode_frame
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class SocketClient(DaemonBase):
    """
    A class for publishing decoded telemetry frames into a queue as a daemon.
    """

    def __init__(
        self,
        socket: SocketType,
        stopper: Callable,
        output_stream: Queue,
        channel_registry: ChannelRegistry,
        app_id: TypePrimitive = None,
        env: TelemetryEnvironment = None,
        mtu: int = DEFAULT_MTU,
    ) -> None:
        """Construct a new socket client."""

        self.socket = socket
        self.mtu = mtu
        self.channel_registry = channel_registry
        name = self.socket.getsockname()
        super().__init__("{}:{}".format(name[0], name[1]), env)
        self.frames = output_stream
        self.expected_id = app_id

        def stop_server() -> None:
            """
            Call provided stopper, then close the socket and signal frame
            queue that frames are over.
            """
            LOG.info("%s: closing listener", self.name)
            stopper()
            socket.close()
            output_stream.put(None)

        self.function["inject_stop"] = stop_server

    def update_mtu(self, new_mtu: int) -> None:
        """
        Update this proxy's understanding of the maximum transmission-unit
        size.
        """

        self.mtu = new_mtu
        LOG.info("%s: mtu set to %d", self.name, new_mtu)

    def run(self, *_, **__) -> None:
        """Read from the listener and enqueue decoded frames."""

        errored = False
        while self.state != DaemonState.STOPPING and not errored:
            try:
                data = self.socket.recv(self.mtu)
                if not data:
                    continue
            except OSError as exc:
                LOG.error(exc)
                errored = True
                continue

            assert self.env is not None
            frame = decode_frame(
                self.channel_registry, data, len(data), self.expected_id
            )
            if frame is not None:
                self.frames.put(frame)
