
"""
vtelem - Test the telemetry server's correctness.
"""

# built-in
import time

# third-party
import requests

# module under test
from vtelem.classes.telemetry_server import TelemetryServer
from vtelem.mtu import get_free_tcp_port


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


def test_telemetry_server_get_types():
    """ Test that the type manifest can be successfully requested. """

    server = TelemetryServer(0.01, 0.10, ("0.0.0.0", 0), 0.25)
    server.start_all()

    # get app id
    result = requests.get(server.get_base_url() + "types?indent=4").json()
    assert all(key in result for key in ["mappings", "types"])

    server.stop_all()


def test_telemetry_server_stop_http():
    """ Test that the server can shutdown from an http request. """

    port = get_free_tcp_port()
    server = TelemetryServer(0.01, 0.10, ("0.0.0.0", port), 0.25,
                             app_id_basis=0.5)
    server.start_all()

    # get app id
    result = requests.get(server.get_base_url() + "id")
    assert result.status_code == requests.codes["ok"]
    app_id = int(result.text)

    # should fail, no 'app_id'
    result = requests.post(server.get_base_url() + "shutdown")
    assert not result.status_code == requests.codes["ok"]

    # should fail, 'app_id' incorrect
    result = requests.post(server.get_base_url() + "shutdown",
                           data={"app_id": 1234})
    assert not result.status_code == requests.codes["ok"]

    # should succeed, 'app_id' correct
    result = requests.post(server.get_base_url() + "shutdown",
                           data={"app_id": app_id})
    assert result.status_code == requests.codes["ok"]

    server.stop_all()
