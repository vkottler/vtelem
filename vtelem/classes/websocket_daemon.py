"""
vtelem - An interface for managing websocket servers.
"""

# built-in
import asyncio
import logging
from typing import Any, Callable, Tuple, Optional

# third-party
import websockets

# internal
from .event_loop_daemon import EventLoopDaemon
from .service_registry import ServiceRegistry
from .telemetry_environment import TelemetryEnvironment

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
        address: Tuple[str, int] = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
        ws_handler: Callable = None,
    ) -> None:
        """Construct a new websocket daemon."""

        super().__init__(name, env, time_keeper)

        # listen on all interfaces, on an arbitrary port by default
        if address is None:
            address = ("0.0.0.0", 0)
        self.address = address
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
            ):  # type: ignore
                pass
            finally:
                LOG.warning(
                    "closing client connection '%s:%d'", raddr[0], raddr[1]
                )

                # handle closing this connection ourselves, because it's
                # difficult to pend on otherwise
                await websocket.close()
                self.wait_poster.release()

        def run_init(
            *_,
            first_start: bool = False,
            service_registry: ServiceRegistry = None,
            **__
        ):
            """
            A function for setting up websocket serving once the thread's
            event loop is established.
            """

            # start serving traffic
            if not self.serving:

                async def routine() -> None:
                    """Capture the server object once we begint serving."""

                    self.server = await websockets.serve(  # type: ignore
                        handler, self.address[0], self.address[1]
                    )
                    if first_start and service_registry is not None:
                        socks = self.server.sockets
                        if socks:
                            addrs = [sock.getsockname() for sock in socks]
                            service_registry.add(self.name, addrs)

                self.eloop.run_until_complete(routine())
                self.serving = True

        self.function["run_init"] = run_init
