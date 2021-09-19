"""
vtelem - Test the websocket telemetry client's correctness.
"""

# built-in
import time

# module under test
from vtelem.client.websocket import WebsocketClient
from vtelem.daemon.websocket_telemetry import (
    WebsocketTelemetryDaemon,
    queue_get,
)
from vtelem.channel.framer import Framer, build_dummy_frame
from vtelem.mtu import DEFAULT_MTU, Host, get_free_tcp_port
from vtelem.stream.writer import default_writer
from vtelem.telemetry.environment import TelemetryEnvironment


def test_websocket_telemetry_client_basic():
    """Test a trivial scenario for a websocket client."""

    # set up an environment
    app_basis = 0.5
    env = TelemetryEnvironment(
        DEFAULT_MTU, metrics_rate=1.0, app_id_basis=app_basis, use_crc=False
    )

    # set up a stream-writer
    writer, frame_queue = default_writer("test_writer", env=env)

    port = get_free_tcp_port()
    server = WebsocketTelemetryDaemon(
        "server", writer, Host("0.0.0.0", port), env
    )

    output = writer.get_queue("client")
    client = WebsocketClient(
        Host("localhost", port),
        output,
        env.channel_registry,
        app_id=Framer.create_app_id(app_basis),
        env=env,
        mtu=DEFAULT_MTU,
    )

    # Test the server closing the connection.
    with writer.booted():
        server.start()
        time.sleep(0.1)
        with client.booted():
            time.sleep(0.1)
            frame_queue.put(build_dummy_frame(64, app_basis))
            assert queue_get(output) is not None
            server.stop()
            time.sleep(5.0)

        with server.booted():
            time.sleep(0.1)

            # Ensure that the connection can be restarted many times.
            for _ in range(3):
                with client.booted():
                    time.sleep(0.2)
                    for _ in range(100):
                        frame_queue.put(build_dummy_frame(64, app_basis))
                        assert queue_get(output) is not None
                    time.sleep(0.2)
