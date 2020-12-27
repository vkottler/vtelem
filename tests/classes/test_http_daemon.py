
"""
vtelem - Test the http daemon's correctness.
"""

# built-in
from http.server import SimpleHTTPRequestHandler

# module under test
from vtelem.classes.http_daemon import HttpDaemon


def test_http_daemon_basic():
    """ Test that the daemon can be managed effectively. """

    daemon = HttpDaemon("test_daemon", ("0.0.0.0", 0),
                        SimpleHTTPRequestHandler)
    assert daemon.start()
    assert daemon.stop()
    assert daemon.close()
    assert not daemon.close()

    daemon = HttpDaemon("test_daemon", ("0.0.0.0", 0),
                        SimpleHTTPRequestHandler)
    assert daemon.start()
    assert daemon.stop()
    assert daemon.start()
    assert daemon.restart()
    assert daemon.stop()
    assert daemon.close()