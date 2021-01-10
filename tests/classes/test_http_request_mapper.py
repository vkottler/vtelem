
"""
vtelem - Test the http request-mapper's correctness.
"""

# built-in
from http.server import BaseHTTPRequestHandler
from typing import Tuple

# third-party
import requests

# module under test
from vtelem.classes.http_daemon import HttpDaemon
from vtelem.classes.http_request_mapper import MapperAwareRequestHandler


def test_http_request_mapper_basic():
    """ Test that the daemon can be managed effectively. """

    daemon = HttpDaemon("test_daemon", handler_class=MapperAwareRequestHandler)

    def error_handle(request: BaseHTTPRequestHandler,
                     _: dict) -> Tuple[bool, str]:
        """ An example handle that always returns error. """

        fstr = "sample error handle ('{}', '{}')"
        return False, fstr.format(request.command, request.path)

    daemon.add_handler("GET", "example", error_handle,
                       "sample handler", {"Random-Header": "test"})

    with daemon.booted():
        result = requests.get(daemon.get_base_url() + "bad")
        assert result.status_code == requests.codes["not_found"]

        result = requests.get(daemon.get_base_url())
        assert result.status_code == requests.codes["ok"]

        result = requests.post(daemon.get_base_url())
        assert result.status_code == requests.codes["not_found"]

        result = requests.head(daemon.get_base_url())
        assert result.status_code == requests.codes["ok"]

        result = requests.head(daemon.get_base_url() + "example")
        assert result.status_code == requests.codes["bad_request"]

        del daemon.server.mapper
        result = requests.get(daemon.get_base_url() + "bad")
        assert result.status_code == requests.codes["not_implemented"]

    assert daemon.close()
