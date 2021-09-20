"""
vtelem - Test the websocket telemetry daemon's correctness.
"""

# built-in
import asyncio
import time

# third-party
import websockets

# module under test
from vtelem.channel.framer import build_dummy_frame
from vtelem.stream import queue_get
from vtelem.stream.writer import default_writer
from vtelem.daemon.websocket_telemetry import WebsocketTelemetryDaemon
from vtelem.mtu import get_free_tcp_port

# internal
from tests import writer_environment


def test_websocket_telemetry_client_fn():
    """
    Test that a created websocket client can connect a few times and decode
    telemetry.
    """

    writer, env = writer_environment()
    daemon = WebsocketTelemetryDaemon("test", writer, env=env)
    client, queue = daemon.client()
    with writer.booted(), daemon.booted():
        time.sleep(0.5)
        for _ in range(3):
            with client.booted():
                time.sleep(0.5)
                for _ in range(10):
                    env.advance_time(10)
                    frame_count = env.dispatch_now()
                    for _ in range(frame_count):
                        assert queue_get(queue) is not None


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

            uri = f"ws://localhost:{port}"
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
