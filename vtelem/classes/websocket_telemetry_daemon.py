"""
vtelem - An interface for managing websocket servers that serve telemetry data.
"""

# built-in
import asyncio
from queue import Queue
from typing import Any, Tuple, Set

# third-party
from websockets.exceptions import WebSocketException

# internal
from .channel_frame import ChannelFrame
from .stream_writer import StreamWriter
from .telemetry_environment import TelemetryEnvironment
from .websocket_daemon import WebsocketDaemon


class WebsocketTelemetryDaemon(WebsocketDaemon):
    """A class for creating telemetry-serving websocket servers."""

    def __init__(
        self,
        name: str,
        writer: StreamWriter,
        address: Tuple[str, int] = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
    ) -> None:
        """Construct a new, telemetry-serving websocket server."""

        async def telem_handle(websocket, _) -> None:
            """
            Write telemetry to this connection, for as long as it's connected.
            """

            frame_queue: Any = Queue()
            queue_id = writer.add_queue(frame_queue)
            should_continue = True
            complete: Set[asyncio.Future] = set()
            pending: Set[asyncio.Future] = set()

            try:
                while should_continue:
                    try:
                        frame: ChannelFrame = frame_queue.get()
                        if frame is None:
                            should_continue = False
                            break

                        complete, pending = await asyncio.wait(
                            [
                                websocket.send(frame.raw()[0]),
                                websocket.wait_closed(),
                            ],
                            return_when=asyncio.FIRST_COMPLETED,
                        )

                        for future in complete:
                            exc = future.exception()
                            if exc is not None:
                                raise exc

                        for pend in pending:
                            pend.cancel()
                    except WebSocketException:
                        should_continue = False
            finally:
                writer.remove_queue(queue_id, False)
                for pend in pending:
                    pend.cancel()

        super().__init__(name, None, address, env, time_keeper, telem_handle)
