
"""
vtelem - Test the telemetry server's correctness.
"""

# built-in
import time

# module under test
from vtelem.classes.telemetry_server import TelemetryServer


def test_telemetry_server_basic():
    """ Test that the telemetry server can boot. """

    server = TelemetryServer(0.01, 0.10, ("0.0.0.0", 0), 0.25)
    assert server.start()
    assert server.daemons.perform_str_all("start")
    time.sleep(0.5)
    server.scale_speed(2.0)
    time.sleep(0.5)
    assert server.daemons.perform_str_all("stop")
    assert server.stop()
