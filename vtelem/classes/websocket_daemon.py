
"""
vtelem - An interface for managing websocket servers.
"""

# built-in
import asyncio
import logging
from typing import Any, Callable, Tuple

# third-party
import websockets

# internal
from .event_loop_daemon import EventLoopDaemon
from .telemetry_environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class WebsocketDaemon(EventLoopDaemon):
    """ A class for creating daemonic websocket request handlers. """

    def __init__(self, name: str, message_consumer: Callable,
                 address: Tuple[str, int] = None,
                 env: TelemetryEnvironment = None,
                 time_keeper: Any = None) -> None:
        """ Construct a new websocket daemon. """

        super().__init__(name, env, time_keeper)

        # listen on all interfaces, on an arbitrary port by default
        if address is None:
            address = ("0.0.0.0", 0)
        self.address = address
        self.serving = False

        async def handler(websocket, path):
            with self.lock:
                self.wait_count += 1
            try:
                async for message in websocket:
                    await message_consumer(websocket, message, path)
            except (asyncio.CancelledError, GeneratorExit):
                LOG.warning("closing client connection '%s'",
                            websocket.remote_address)

            # handle closing this connection ourselves, because it's difficult
            # to pend on otherwise
            await websocket.close()

            with self.lock:
                self.wait_count -= 1
            self.wait_poster.release()

        def run_init(*_, **__):
            """
            A function for setting up websocket serving once the thread's
            event loop is established.
            """

            # start serving traffic
            if not self.serving:
                routine = websockets.serve(handler, self.address[0],
                                           self.address[1])
                self.eloop.run_until_complete(routine)
                self.serving = True

        self.function["run_init"] = run_init
