"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         websocket connection.
"""

# built-in
from asyncio import Task, ensure_future
import logging
from queue import Queue
from typing import Any, Optional

# third-party
import websockets

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.client import TelemetryClient
from vtelem.daemon import DaemonState
from vtelem.daemon.event_loop import EventLoopDaemon
from vtelem.mtu import DEFAULT_MTU, Host
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class WebsocketClient(EventLoopDaemon, TelemetryClient):
    """
    A class for consuming telemetry data from a websocket connection to a
    specific host.
    """

    def __init__(
        self,
        host: Host,
        output_stream: Queue,
        channel_registry: ChannelRegistry,
        secure: bool = False,
        uri_path: str = "",
        app_id: TypePrimitive = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
        mtu: int = DEFAULT_MTU,
    ) -> None:
        """Construct a new websocket-telemetry client."""

        name_str = f"{host.address}:{host.port}"
        EventLoopDaemon.__init__(self, name_str, env, time_keeper)
        TelemetryClient.__init__(
            self, name_str, output_stream, channel_registry, app_id, mtu
        )
        self.connected: bool = False
        self.task: Optional[Task] = None

        async def connection_handle(websocket, _) -> None:
            """Handle a websocket-client connection."""

            frame_size = new_default("count")
            assert self.env is not None
            try:
                while self.state != DaemonState.STOPPING:
                    self.handle_frames(
                        self.processor.process(
                            await websocket.recv(), frame_size, self.mtu
                        )
                    )
            except websockets.exceptions.WebSocketException as exc:
                LOG.error("Exception while awaiting frames: %s.", exc)

        async def connect() -> None:
            """Establish a connection and wait for the handler to complete."""

            uri_prefix = f"{'wss' if secure else 'ws'}://"
            uri = f"{uri_prefix}{host.address}:{host.port}{uri_path}"
            LOG.info("Connecting to '%s'.", uri)
            try:
                with self.lock:
                    self.wait_count += 1
                self.connected = True
                async with websockets.connect(  # type: ignore
                    uri, close_timeout=1
                ) as websocket:
                    await connection_handle(websocket, uri_path)
            finally:
                self.wait_poster.release()
                self.connected = False

        def run_init(*_, **__) -> None:
            """
            Prime the event loop to establish a new connection if we don't
            have an active one.
            """

            if not self.connected:
                ensure_future(connect(), loop=self.eloop)

        self.function["run_init"] = run_init
