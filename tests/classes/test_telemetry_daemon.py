"""
vtelem - Test the correctness of the telemetry daemon.
"""

# module under test
from vtelem.classes.telemetry_daemon import TelemetryDaemon
from vtelem.classes.time_keeper import TimeKeeper


def test_telemetry_daemon_basic():
    """Test basic starting-up of a telemetry daemon."""

    keeper = TimeKeeper("time", 0.05)
    daemon = TelemetryDaemon("test_telemetry", 2 ** 8, 0.5, keeper, 1.0)
    assert daemon.env is not None
    assert keeper.start()
    assert daemon.start()
    keeper.sleep(1.0)
    assert daemon.get_enum_metric(daemon.get_metric_name("state")) == "running"
    keeper.sleep(1.0)
    assert daemon.stop()
    assert keeper.stop()
