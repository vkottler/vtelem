"""
vtelem - Test the tcp telemetry daemon's correctness.
"""

# built-in
import socket
import time

# module under test
from vtelem.channel.framer import build_dummy_frame
from vtelem.classes.metered_queue import MeteredQueue
from vtelem.classes.stream_writer import default_writer
from vtelem.client.tcp import TcpClient
from vtelem.daemon.tcp_telemetry import TcpTelemetryDaemon
from vtelem.frame.framer import Framer
from vtelem.mtu import Host
from vtelem.telemetry.environment import TelemetryEnvironment


def test_tcp_telemetry_daemon_boot():
    """Test starting and stopping the server."""

    writer, _ = default_writer("frames")
    env = TelemetryEnvironment(64, metrics_rate=1.0)
    daemon = TcpTelemetryDaemon("test", writer, env)
    for _ in range(5):
        with daemon.booted():
            assert daemon.address[0] is not None
            assert daemon.address[1] is not None


def test_tcp_telemetry_many_clients():
    """Connect many clients, send each a few frames."""

    writer, frame_queue = default_writer("frames")
    env = TelemetryEnvironment(64, metrics_rate=1.0)
    daemon = TcpTelemetryDaemon("test", writer, env)
    for _ in range(3):
        with daemon.booted():
            sockets = []
            for _ in range(25):
                sockets.append(socket.create_connection(daemon.address))
            for _ in range(5):
                frame_queue.put(build_dummy_frame(1024))
            for sock in sockets:
                sock.close()


def test_tcp_telemetry_real_client():
    """Test that a real client can receive and decode frames."""

    # create the environment and register its frame queue
    env = TelemetryEnvironment(64, metrics_rate=1.0)
    writer, _ = default_writer("frames", env=env, queue=env.frame_queue)

    # create a tcp-daemon for this environment
    daemon = TcpTelemetryDaemon("test", writer, env)

    with writer.booted(), daemon.booted():
        time.sleep(0.1)

        # create client
        out_queue = MeteredQueue("out", env)
        client_addr = Host(*daemon.address)
        client = TcpClient(
            client_addr,
            out_queue,
            env.channel_registry,
            env.app_id,
            env,
        )
        with client.booted():
            time.sleep(0.5)
            for _ in range(10):
                # advance time, dispatch to generate out-going frames
                env.advance_time(10)
                frame_count = env.dispatch_now()
                for _ in range(frame_count):
                    assert out_queue.get() is not None


def test_tcp_telemetry_bad_app_id():
    """Test cient behavior when the application identifier doesn't match."""

    # create the environment and register its frame queue
    basis = 0.5
    env = TelemetryEnvironment(64, metrics_rate=1.0, app_id_basis=basis)
    writer, _ = default_writer("frames", env=env, queue=env.frame_queue)

    # create a tcp-daemon for this environment
    daemon = TcpTelemetryDaemon("test", writer, env)

    with writer.booted(), daemon.booted():
        time.sleep(0.1)

        # create client
        out_queue = MeteredQueue("out", env)
        client_addr = Host(*daemon.address)
        client = TcpClient(
            client_addr,
            out_queue,
            env.channel_registry,
            Framer.create_app_id(basis + 0.1),  # use an incorrect app-id
            env,
        )
        with client.booted():
            time.sleep(0.5)
            for _ in range(10):
                # advance time, dispatch to generate out-going frames
                env.advance_time(10)
                frame_count = env.dispatch_now()
                for _ in range(frame_count):
                    time.sleep(0.05)

                    # we shouldn't get a frame if we had an app-id mis-match
                    assert out_queue.empty()


def test_tcp_telemetry_simple_client():
    """Transfer data from server to client."""

    writer, frame_queue = default_writer("frames")
    env = TelemetryEnvironment(64, metrics_rate=1.0)
    daemon = TcpTelemetryDaemon("test", writer, env)
    frame_size = 1024
    with writer.booted(), daemon.booted():
        sock = socket.create_connection(daemon.address)
        time.sleep(0.1)
        for _ in range(25):
            frame = build_dummy_frame(frame_size)
            frame_queue.put(frame)

            data = sock.recv(frame_size + writer.overhead)
            assert len(data) == frame_size + writer.overhead

        # close the socket, try to write the broken pipe to force the stream
        # writer to un-register it
        sock.close()
        for _ in range(5):
            frame_queue.put(frame)

        # connect another client, make sure server-close closes this connection
        sock = socket.create_connection(daemon.address)
        time.sleep(0.1)
        for _ in range(25):
            frame = build_dummy_frame(frame_size)
            frame_queue.put(frame)
            data = sock.recv(frame_size + writer.overhead)
            assert len(data) == frame_size + writer.overhead
