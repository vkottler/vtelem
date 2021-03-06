"""
vtelem - Test the websocket telemetry daemon's correctness.
"""

# built-in
import asyncio
import time

# third-party
import websockets

# module under test
from vtelem.classes.channel_framer import build_dummy_frame
from vtelem.classes.stream_writer import default_writer
from vtelem.classes.websocket_telemetry_daemon import (
    WebsocketTelemetryDaemon,
    queue_get,
)
from vtelem.mtu import get_free_tcp_port


def test_websocket_telemetry_daemon_server_close_first():
    """
    Test that we can successfully close server ends of connections and still
    shutdown gracefully.
    """

    writer, frames = default_writer("frames")
    assert queue_get(frames, 0.1) is None
    port = get_free_tcp_port()
    daemon = WebsocketTelemetryDaemon("test", writer, ("0.0.0.0", port))

    num_frames = 10
    with writer.booted(), daemon.booted():
        time.sleep(0.1)

        async def read_test():
            """
            Read some frames and then expect the server end of the connection
            to close first.
            """

            uri = "ws://localhost:{}".format(port)
            async with websockets.connect(uri, close_timeout=1) as websocket:
                time.sleep(0.1)

                # prepare frames for transfer
                for elem in [build_dummy_frame(64) for _ in range(num_frames)]:
                    frames.put(elem)

                for _ in range(num_frames):
                    frame = await websocket.recv()
                    assert frame

                # close the server end of the connection
                assert daemon.close_clients() == 1
                try:
                    await websocket.recv()
                    assert False
                except websockets.exceptions.ConnectionClosedOK:
                    pass

        asyncio.get_event_loop().run_until_complete(read_test())
