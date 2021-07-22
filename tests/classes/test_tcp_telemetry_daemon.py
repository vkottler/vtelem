"""
vtelem - Test the tcp telemetry daemon's correctness.
"""

# module under test
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
