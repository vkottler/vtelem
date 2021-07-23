"""
vtelem - Test the tcp telemetry daemon's correctness.
"""

# built-in
import socket
import time

# module under test
from vtelem.classes.channel_framer import build_dummy_frame
from vtelem.classes.stream_writer import default_writer
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.classes.tcp_telemetry_daemon import TcpTelemetryDaemon


def test_tcp_telemetry_daemon_boot():
    """Test starting and stopping the server."""

    writer, _ = default_writer("frames")
    env = TelemetryEnvironment(64, metrics_rate=1.0)
    daemon = TcpTelemetryDaemon("test", writer, env)
    for _ in range(5):
        with daemon.booted():
            assert daemon.address[0] is not None
            assert daemon.address[1] is not None


def test_tcp_telemetry_simple_client():
    """Transfer data from server to client."""

    writer, frame_queue = default_writer("frames")
    env = TelemetryEnvironment(64, metrics_rate=1.0)
    daemon = TcpTelemetryDaemon("test", writer, env)
    with writer.booted(), daemon.booted():
        sock = socket.create_connection(daemon.address)
        time.sleep(0.1)
        for _ in range(25):
            frame = build_dummy_frame(1024)
            frame_queue.put(frame)
            data = sock.recv(1024)
            assert len(data) == 1024

        # close the socket, try to write the broken pipe to force the stream
        # writer to un-register it
        sock.close()
        for _ in range(5):
            frame_queue.put(frame)

        # connect another client, make sure server-close closes this connection
        sock = socket.create_connection(daemon.address)
        time.sleep(0.1)
        for _ in range(25):
            frame = build_dummy_frame(1024)
            frame_queue.put(frame)
            data = sock.recv(1024)
            assert len(data) == 1024
