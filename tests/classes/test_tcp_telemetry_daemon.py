"""
vtelem - Test the tcp telemetry daemon's correctness.
"""

# module under test
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.classes.tcp_telemetry_daemon import TcpTelemetryDaemon


def test_tcp_telemetry_daemon_boot():
    """Test starting and stopping the server."""

    env = TelemetryEnvironment(64, metrics_rate=1.0)
    daemon = TcpTelemetryDaemon("test", env)
    for _ in range(5):
        with daemon.booted():
            assert daemon.address[0] is not None
            assert daemon.address[1] is not None
