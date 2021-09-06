"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         socket.
"""

# built-in
import logging
from queue import Queue
from socket import timeout, SocketType
from typing import Callable

# internal
from vtelem.mtu import DEFAULT_MTU
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.client import TelemetryClient
from vtelem.daemon import DaemonBase, DaemonState
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class SocketClient(DaemonBase, TelemetryClient):
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
        name = self.socket.getsockname()
        name_str = "{}:{}".format(name[0], name[1])
        TelemetryClient.__init__(
            self, name_str, output_stream, channel_registry, app_id, mtu
        )
        DaemonBase.__init__(self, name_str, env)

        def stop_server() -> None:
            """
            Call provided stopper, then close the socket and signal frame
            queue that frames are over.
            """
            LOG.info("%s: closing socket reader", self.name)
            stopper()
            socket.close()
            output_stream.put(None)

        self.function["inject_stop"] = stop_server

    def run(self, *_, **__) -> None:
        """Read from the listener and enqueue decoded frames."""

        frame_size = new_default("count")
        assert self.env is not None

        while self.state != DaemonState.STOPPING:
            try:
                raw_data = self.socket.recv(
                    self.mtu + frame_size.type.value.size
                )
                if not raw_data:
                    LOG.info("%s: stream ended", self.name)
                    break
                self.handle_frames(
                    self.processor.process(raw_data, frame_size, self.mtu)
                )
            except timeout:
                pass
            except OSError as exc:
                LOG.error("%s: %s", self.name, exc)
                break
