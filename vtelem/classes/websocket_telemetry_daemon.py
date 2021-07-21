"""
vtelem - An interface for managing websocket servers that serve telemetry data.
"""

# built-in
import asyncio
from queue import Empty, Queue
from typing import Any, List, Tuple, Set, Optional

# third-party
from websockets.exceptions import WebSocketException

# internal
from .channel_frame import ChannelFrame
from .stream_writer import StreamWriter
from .telemetry_environment import TelemetryEnvironment
from .websocket_daemon import WebsocketDaemon


def queue_get(queue: Queue, timeout: int = 2) -> Optional[Any]:
    """
    Wrap a de-queue operation into one that will return None if the timeout
    is met.
    """

    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None


class WebsocketTelemetryDaemon(WebsocketDaemon):
    """A class for creating telemetry-serving websocket servers."""

    def close_clients(self) -> int:
        """
        Attempt to remove all active client-writing queues from the stream
        writer. This should initiate our side of the connections to begin
        closing.
        """

        closed = 0
        with self.lock:
            for queue_id in self.active_client_queues:
                if self.writer.remove_queue(queue_id):
                    closed += 1
        return closed

    def __init__(
        self,
        name: str,
        writer: StreamWriter,
        address: Tuple[str, int] = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
    ) -> None:
        """Construct a new, telemetry-serving websocket server."""

        self.writer = writer
        self.active_client_queues: List[int] = []

        async def telem_handle(websocket, _) -> None:
            """
            Write telemetry to this connection, for as long as it's connected.
            """

            frame_queue: Any = Queue()
            with self.lock:
                queue_id = self.writer.add_queue(frame_queue)
                self.active_client_queues.append(queue_id)
            should_continue = True
            complete: Set[asyncio.Future] = set()
            pending: Set[asyncio.Future] = set()

            try:
                while should_continue:
                    try:
                        frame: Optional[ChannelFrame] = queue_get(frame_queue)
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
                self.writer.remove_queue(queue_id, False)
                for pend in pending:
                    pend.cancel()

        super().__init__(name, None, address, env, time_keeper, telem_handle)
