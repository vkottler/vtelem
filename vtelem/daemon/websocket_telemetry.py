"""
vtelem - An interface for managing websocket servers that serve telemetry data.
"""

# built-in
import asyncio
from queue import Empty, Queue
from typing import Any, Set, Optional, Tuple

# third-party
from websockets.exceptions import WebSocketException

# internal
from vtelem.classes.stream_writer import StreamWriter, QueueClientManager
from vtelem.client.websocket import WebsocketClient
from vtelem.daemon.websocket import WebsocketDaemon
from vtelem.frame.channel import ChannelFrame
from vtelem.mtu import Host, DEFAULT_MTU
from vtelem.telemetry.environment import TelemetryEnvironment


def queue_get(queue: Queue, timeout: int = 2) -> Optional[Any]:
    """
    Wrap a de-queue operation into one that will return None if the timeout
    is met.
    """

    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None


class WebsocketTelemetryDaemon(QueueClientManager, WebsocketDaemon):
    """A class for creating telemetry-serving websocket servers."""

    def __init__(
        self,
        name: str,
        writer: StreamWriter,
        address: Host = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
    ) -> None:
        """Construct a new, telemetry-serving websocket server."""

        QueueClientManager.__init__(self, name, writer)

        async def telem_handle(websocket, _) -> None:
            """
            Write telemetry to this connection, for as long as it's connected.
            """

            queue_id, frame_queue = self.add_client_queue(
                Host(*websocket.remote_address)
            )
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
                                websocket.send(frame.with_size_header()[0]),
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

        WebsocketDaemon.__init__(
            self, name, None, address, env, time_keeper, telem_handle
        )

    def client(
        self,
        mtu: int = DEFAULT_MTU,
        uri_path: str = "",
        time_keeper: Any = None,
    ) -> Tuple[WebsocketClient, Queue]:
        """Create a connected websocket client from this daemon."""

        assert self.env is not None
        queue = self.writer.get_queue()
        return (
            WebsocketClient(
                self.address,
                queue,
                self.env.channel_registry,
                self.secure,
                uri_path,
                self.env.app_id,
                self.env,
                time_keeper,
                mtu,
            ),
            queue,
        )
