
"""
vtelem - Test the telemetry proxy's correctness.
"""

# built-in
from queue import Queue
import time

# module under test
from vtelem.classes.channel_framer import create_app_id, build_dummy_frame
from vtelem.classes.stream_writer import StreamWriter
from vtelem.classes.telemetry_proxy import TelemetryProxy
from vtelem.classes.udp_client_manager import UdpClientManager


def test_telemetry_proxy_basic():
    """ Test that valid frames can be decoded. """

    # set up the proxy
    frames = Queue()
    app_basis = 0.5
    proxy = TelemetryProxy(("localhost", 0), frames,
                           create_app_id(app_basis))

    # set up a stream-writer
    frame_queue = Queue()
    writer = StreamWriter("test_writer", frame_queue)
    manager = UdpClientManager(writer)
    client = manager.add_client(("localhost", proxy.socket.getsockname()[1]))

    proxy.start()

    # write some frames
    with writer.booted():
        for _ in range(5):
            frame_queue.put(build_dummy_frame(client[1], app_basis))
    manager.remove_client(client[0])

    time.sleep(1.0)

    proxy.stop()
