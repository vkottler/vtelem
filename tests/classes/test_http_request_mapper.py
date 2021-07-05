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
from vtelem.classes.http_request_mapper import (
    MapperAwareRequestHandler,
    parse_content_type,
    get_multipart_boundary,
)


def error_handle(request: BaseHTTPRequestHandler, _: dict) -> Tuple[bool, str]:
    """An example handle that always returns error."""

    fstr = "sample error handle ('{}', '{}')"
    return False, fstr.format(request.command, request.path)


def test_http_reqest_mapper_post():
    """Test POST requests with 'multipart/form-data' encoding."""

    daemon = HttpDaemon("test_daemon", handler_class=MapperAwareRequestHandler)

    def post_handle(_: BaseHTTPRequestHandler, data: dict) -> Tuple[bool, str]:
        """Example request handler."""

        assert "parts" in data
        assert len(data["parts"]) == 3
        return True, ""

    daemon.add_handler("POST", "example", post_handle)
    with daemon.booted():
        result = requests.post(
            daemon.get_base_url() + "example",
            files={"a": "a", "b": "b", "c": "c"},
        )
        assert result.status_code == requests.codes["ok"]

    assert parse_content_type("") is None
    assert get_multipart_boundary({}) is None


def test_http_request_mapper_basic():
    """Test that the daemon can be managed effectively."""

    daemon = HttpDaemon("test_daemon", handler_class=MapperAwareRequestHandler)
    daemon.add_handler(
        "GET",
        "example",
        error_handle,
        "sample handler",
        {"Random-Header": "test"},
    )

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
