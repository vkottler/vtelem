"""
vtelem - An interface for managing websocket servers.
"""

# built-in
import asyncio
import logging
from typing import Any, Callable, Optional

# third-party
import websockets

# internal
from vtelem.daemon.event_loop import EventLoopDaemon
from vtelem.mtu import Host, get_free_tcp_port
from vtelem.registry.service import ServiceRegistry
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


def create_default_handler(message_consumer: Callable) -> Callable:
    """Create a default websocket-connection handler."""

    async def handler(websocket, path) -> None:
        """
        For every message from this connection, call the message consumer.
        """

        async for message in websocket:
            await message_consumer(websocket, message, path)

    return handler


class WebsocketDaemon(EventLoopDaemon):
    """A class for creating daemonic websocket request handlers."""

    def __init__(
        self,
        name: str,
        message_consumer: Optional[Callable],
        address: Host = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
        ws_handler: Callable = None,
        secure: bool = False,
    ) -> None:
        """Construct a new websocket daemon."""

        super().__init__(name, env, time_keeper)

        # listen on all interfaces, on an arbitrary port by default
        if address is None:
            address = Host(port=get_free_tcp_port())
        self.address = address
        self.secure = secure
        self.server = None
        self.serving = False

        if ws_handler is None:
            assert message_consumer is not None
            ws_handler = create_default_handler(message_consumer)

        async def handler(websocket, path) -> None:
            with self.lock:
                self.wait_count += 1

            laddr = websocket.local_address
            raddr = websocket.remote_address
            fstr = "connection ('%s') opened '%s:%d' -> '%s:%d'"
            LOG.info(fstr, path, laddr[0], laddr[1], raddr[0], raddr[1])

            try:
                assert ws_handler is not None
                await ws_handler(websocket, path)
            except (
                asyncio.CancelledError,
                GeneratorExit,
                websockets.exceptions.WebSocketException,
            ):
                pass
            finally:
                LOG.warning(
                    "closing client connection '%s:%d'", raddr[0], raddr[1]
                )
                # post first, if we never finish closing the connection that's
                # okay
                self.wait_poster.release()
                await websocket.close()

        def run_init(
            *_,
            first_start: bool = False,
            service_registry: ServiceRegistry = None,
            **__
        ) -> None:
            """
            A function for setting up websocket serving once the thread's
            event loop is established.
            """

            # start serving traffic
            if not self.serving:

                async def routine() -> None:
                    """Capture the server object once we begint serving."""

                    self.server = await websockets.serve(  # type: ignore
                        handler,
                        self.address[0],
                        self.address[1],
                        close_timeout=1,
                    )
                    if first_start and service_registry is not None:
                        socks = self.server.sockets
                        if socks:
                            addrs = [sock.getsockname() for sock in socks]
                            service_registry.add(self.name, addrs)

                self.eloop.run_until_complete(routine())
                self.serving = True

        self.function["run_init"] = run_init
