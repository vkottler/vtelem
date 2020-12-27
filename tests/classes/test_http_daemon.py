
"""
vtelem - Test the http daemon's correctness.
"""

# third-party
import requests

# module under test
from vtelem.classes.http_daemon import HttpDaemon


def test_http_daemon_basic():
    """ Test that the daemon can be managed effectively. """

    daemon = HttpDaemon("test_daemon")
    assert daemon.start()
    result = requests.get(daemon.get_base_url())
    assert result.status_code == requests.codes["ok"]
    assert daemon.stop()
    assert daemon.close()
    assert not daemon.close()

    daemon = HttpDaemon("test_daemon")
    assert daemon.start()
    assert daemon.stop()
    assert daemon.start()
    assert daemon.restart()
    assert daemon.stop()
    assert daemon.close()
