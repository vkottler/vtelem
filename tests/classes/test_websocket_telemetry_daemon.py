"""
vtelem - Test the websocket telemetry daemon's correctness.
"""

# built-in
import asyncio
from queue import Queue
import time

# third-party
import websockets

# module under test
from vtelem.classes.channel_framer import build_dummy_frame
from vtelem.classes.stream_writer import StreamWriter
from vtelem.classes.websocket_telemetry_daemon import WebsocketTelemetryDaemon
from vtelem.mtu import get_free_tcp_port


def test_websocket_telemetry_daemon_server_close_first():
    """
    Test that we can successfully close server ends of connections and still
    shutdown gracefully.
    """

    frames = Queue()
    writer = StreamWriter("frames", frames)
    port = get_free_tcp_port()
    daemon = WebsocketTelemetryDaemon("test", writer, ("0.0.0.0", port))

    num_frames = 10
    with daemon.booted(), writer.booted():
        time.sleep(0.1)

        async def read_test():
            """
            Read some frames and then expect the server end of the connection
            to close first.
            """

            uri = "ws://localhost:{}".format(port)
            async with websockets.connect(uri) as websocket:

                # transfer some frames
                for elem in [build_dummy_frame(64) for _ in range(num_frames)]:
                    frames.put(elem)
                    frame = await websocket.recv()
                    assert frame

                # close the server end of the connection
                assert daemon.close_clients() == 1
                try:
                    await websocket.recv()
                    assert False
                except websockets.exceptions.ConnectionClosedOK:
                    pass
                finally:
                    await websocket.wait_closed()

        asyncio.get_event_loop().run_until_complete(read_test())
        time.sleep(0.2)
