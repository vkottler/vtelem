
"""
vtelem - An interface for managing websocket servers that serve telemetry data.
"""

# built-in
import asyncio
from queue import Queue, Empty
from typing import Any, List, Tuple

# third-party
import websockets

# internal
from .channel_frame import ChannelFrame
from .stream_writer import StreamWriter
from .telemetry_environment import TelemetryEnvironment
from .websocket_daemon import WebsocketDaemon


class WebsocketTelemetryDaemon(WebsocketDaemon):
    """ A class for creating telemetry-serving websocket servers. """

    def __init__(self, name: str, writer: StreamWriter,
                 address: Tuple[str, int] = None,
                 env: TelemetryEnvironment = None,
                 time_keeper: Any = None) -> None:
        """ Construct a new, telemetry-serving websocket server. """

        async def telem_handle(websocket, _) -> None:
            """
            Write telemetry to this connection, for as long as it's connected.
            """

            frame_queue: Any = Queue()
            queue_id = writer.add_queue(frame_queue)
            should_continue = True

            try:
                while should_continue:
                    try:
                        frames: List[ChannelFrame] = []
                        try:
                            while True:
                                frames.append(frame_queue.get_nowait())
                        except Empty:
                            pass

                        for frame in frames:
                            if frame is None:
                                should_continue = False
                                break
                            await websocket.send(frame.raw()[0])

                        if should_continue:
                            await asyncio.wait_for(websocket.recv(),
                                                   timeout=0.1)
                    except asyncio.exceptions.TimeoutError:
                        pass
                    except websockets.exceptions.WebSocketException:
                        should_continue = False
            finally:
                writer.remove_queue(queue_id, False)

        super().__init__(name, None, address, env, time_keeper, telem_handle)
