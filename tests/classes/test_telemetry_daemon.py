
"""
vtelem - Test the correctness of the telemetry daemon.
"""

# module under test
from vtelem.classes.telemetry_daemon import TelemetryDaemon
from vtelem.classes.time_keeper import TimeKeeper


def test_telemetry_daemon_basic():
    """ Test basic starting-up of a telemetry daemon. """

    keeper = TimeKeeper(0.05)
    daemon = TelemetryDaemon(2 ** 8, 0.5, keeper, 1.0)
    assert keeper.start()
    assert daemon.start()
    keeper.sleep(1.0)
    assert daemon.get_enum_metric("daemon") == "running"
    keeper.sleep(1.0)
    assert daemon.stop()
    assert keeper.stop()
