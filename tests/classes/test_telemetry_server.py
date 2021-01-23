
"""
vtelem - Test the telemetry server's correctness.
"""

# built-in
import asyncio
import json
import time

# third-party
import requests
import websockets

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

    # add  a client
    server.udp_clients.add_client(("0.0.0.0", 0))

    # get app id
    result = requests.get(server.get_base_url() + "types?indent=4").json()
    assert all(key in result for key in ["mappings", "types"])

    server.stop_all()


async def ws_command(wsock, msg: str, expect: bool):
    """ Test an individual websocket command. """

    await wsock.send(msg)
    rsp_data = json.loads(await wsock.recv())
    assert rsp_data["success"] == expect
    return rsp_data["message"]


async def ws_command_dict(wsock, msg: dict, expect: bool):
    """ Test a websocket command from dict data. """

    return await ws_command(wsock, json.dumps(msg), expect)


def test_telemetry_server_ws_commands():
    """ Test that websocket commands are supported by the server. """

    port = get_free_tcp_port()
    server = TelemetryServer(0.01, 0.10, None, 0.25,
                             websocket_cmd_address=("0.0.0.0", port))
    server.start_all()

    async def help_test():
        """ Send some commands to the server. """

        uri = "ws://localhost:{}".format(port)
        async with websockets.connect(uri) as websocket:

            # test invalid json
            await ws_command(websocket, "{'command': 'help'}", False)

            # test valid json
            await ws_command_dict(websocket, {"command": "help"}, True)

            # test udp client commands
            data = {}
            cmd = {"command": "udp", "data": data}
            await ws_command_dict(websocket, cmd, False)
            data["operation"] = "asdf"
            await ws_command_dict(websocket, cmd, False)
            data["operation"] = "list"
            await ws_command_dict(websocket, cmd, True)

            # add a client
            data["operation"] = "add"
            await ws_command_dict(websocket, cmd, False)
            data["host"] = "localhost"
            data["port"] = 0
            await ws_command_dict(websocket, cmd, True)
            del data["host"]
            del data["port"]

            # list the single client
            data["operation"] = "list"
            clients = json.loads(await ws_command_dict(websocket, cmd, True))
            for client in clients:
                data["id"] = int(client)
                await ws_command_dict(websocket, cmd, True)
            data["id"] = -1
            await ws_command_dict(websocket, cmd, False)

            # remove the clients
            data["operation"] = "remove"
            del data["id"]
            await ws_command_dict(websocket, cmd, False)
            data["id"] = -1
            await ws_command_dict(websocket, cmd, False)

            for client in clients:
                data["id"] = int(client)
                await ws_command_dict(websocket, cmd, True)

    asyncio.get_event_loop().run_until_complete(help_test())

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
