"""
vtelem - Test the http daemon's correctness.
"""

# built-in
from multiprocessing import Process
import os
import signal
import time

# third-party
import requests

# internal
from tests.resources import get_resource

# module under test
from vtelem.classes.http_daemon import HttpDaemon


def test_http_daemon_serve():
    """Test the simplified 'serve' interface."""

    daemon = HttpDaemon("test_daemon1")

    def thread_fn(*args, **kwargs) -> int:
        """An example 'main thread' that doesn't do anything."""

        print(args)
        print(kwargs)
        return 0

    assert daemon.serve(main_thread=thread_fn) == 0

    def threaded_server() -> None:
        """Serve the daemon using the default main-thread function."""

        dmon = HttpDaemon("test_daemon2")
        assert dmon.serve() == 0

    proc = Process(target=threaded_server)
    proc.start()
    time.sleep(1.0)
    os.kill(proc.pid, signal.SIGINT)
    proc.join()


def test_http_daemon_with_tls():
    """Test that a daemon works with secure-socket layer enabled."""

    daemon = HttpDaemon("test_daemon")
    daemon.use_tls(get_resource("test.key"), get_resource("test.cert"))
    with daemon.booted():
        result = requests.get(daemon.get_base_url(), verify=False)
        assert result.status_code == requests.codes["ok"]
    assert daemon.close()


def test_http_daemon_basic():
    """Test that the daemon can be managed effectively."""

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
