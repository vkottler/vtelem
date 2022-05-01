"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         socket.
"""

# built-in
import logging
from queue import Queue
from socket import SocketType, timeout
from typing import Callable

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.client import TelemetryClient
from vtelem.daemon import DaemonBase, DaemonState
from vtelem.mtu import DEFAULT_MTU
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class SocketClient(DaemonBase, TelemetryClient):
    """
    A class for publishing decoded telemetry frames into a queue as a daemon.
    """

    def __init__(
        self,
        sock: SocketType,
        stopper: Callable,
        output_stream: Queue,
        channel_registry: ChannelRegistry,
        app_id: TypePrimitive = None,
        env: TelemetryEnvironment = None,
        mtu: int = DEFAULT_MTU,
    ) -> None:
        """Construct a new socket client."""

        self.socket = sock
        TelemetryClient.__init__(
            self, "", output_stream, channel_registry, app_id, mtu
        )
        DaemonBase.__init__(self, "", env)
        self.update_name(self.socket)

        def closer() -> None:
            """
            Close the socket and signal the output stream that the stream has
            ended.
            """

            self.socket.close()
            output_stream.put(None)

        self.function["close"] = closer

        def stop_server() -> None:
            """
            Call provided stopper, then close the socket and signal frame
            queue that frames are over.
            """
            LOG.info("%s: closing socket reader", self.name)
            stopper()
            self.close()

        self.function["inject_stop"] = stop_server

    def update_name(self, sock: SocketType) -> None:
        """Set a new name attribute based on the provided socket."""

        name = sock.getsockname()
        self.name = f"{name[0]}:{name[1]}"

    def close(self) -> None:
        """Attempt to close this client connection."""

        self.function["close"]()

    def run(self, *_, **__) -> None:
        """Read from the listener and enqueue decoded frames."""

        # If an 'init' function is provided, re-initialize the socket.
        if "init" in self.function:
            self.socket = self.function["init"](self.socket)
            self.update_name(self.socket)

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
