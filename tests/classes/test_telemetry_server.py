"""
vtelem - Test the telemetry server's correctness.
"""

# built-in
import asyncio
import json
import time
from typing import Tuple

# third-party
import requests
import websockets

# module under test
from vtelem.frame import FRAME_OVERHEAD
from vtelem.mtu import Host, get_free_tcp_port
from vtelem.telemetry.server import TelemetryServer
from vtelem.types.telemetry_server import Service, default_services


def test_telemetry_server_basic():
    """Test that the telemetry server can boot."""

    server = TelemetryServer(0.01, 0.10, 0.25)
    assert server.daemons.get("stream").get_queue("test")
    with server.booted():
        time.sleep(2.0)
        server.scale_speed(2.0)
        time.sleep(2.0)


def test_telemetry_server_get_types():
    """Test that the type manifest can be successfully requested."""

    server = TelemetryServer(0.01, 0.10, 0.25)
    with server.booted():
        # add  a client
        server.udp_clients.add_client(Host())

        # get app id
        cmd_str = "types?indent=4"
        result = requests.get(
            server.get_base_url() + cmd_str, timeout=1.0
        ).json()
        assert all(key in result for key in ["mappings", "types"])

        # run the 'help' command
        cmd_str = "command"
        requests.get(server.get_base_url() + cmd_str, timeout=1.0)
        cmd_str = "command?command=help&indent=4"
        result = requests.get(
            server.get_base_url() + cmd_str, timeout=1.0
        ).json()
        assert result

        # get registries
        result = requests.get(
            server.get_base_url() + "registries", timeout=1.0
        ).json()
        assert result


async def ws_command(wsock, msg: str, expect: bool) -> Tuple[bool, str]:
    """Test an individual websocket command."""

    rsp_data: dict = {"success": False, "message": "send failed"}
    request_success = False
    try:
        await wsock.send(msg)
        rsp_data = json.loads(await wsock.recv())
        request_success = True
    except websockets.exceptions.WebSocketException:
        pass
    return (
        (rsp_data["success"] == expect and request_success),
        rsp_data["message"],
    )


async def ws_command_dict(wsock, msg: dict, expect: bool) -> Tuple[bool, str]:
    """Test a websocket command from dict data."""

    return await ws_command(wsock, json.dumps(msg), expect)


def test_telemetry_server_ws_telemetry():
    """Test that websocket telemetry is supported by the server."""

    port = get_free_tcp_port()
    server = TelemetryServer(
        0.01,
        0.10,
        0.25,
        services=default_services(
            websocket_telemetry=Service(
                "websocket_telemetry", Host("0.0.0.0", port)
            )
        ),
    )
    with server.booted():
        time.sleep(0.1)

        async def telemetry_test():
            """Send some commands to the server."""

            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, close_timeout=1) as websocket:
                time.sleep(0.1)
                for _ in range(10):
                    frame = await websocket.recv()
                    telem = server.daemons.get("telemetry")
                    result = telem.decode_frame(
                        frame[FRAME_OVERHEAD:],
                        len(frame) - FRAME_OVERHEAD,
                        telem.app_id,
                    )
                    assert result is not None

        for _ in range(5):
            asyncio.get_event_loop().run_until_complete(telemetry_test())


def test_telemetry_server_ws_commands():
    """Test that websocket commands are supported by the server."""

    port = get_free_tcp_port()
    server = TelemetryServer(
        0.01,
        0.10,
        0.25,
        services=default_services(
            websocket_command=Service(
                "websocket_command", Host("0.0.0.0", port)
            )
        ),
    )
    with server.booted():
        time.sleep(0.1)
        fails = 0

        async def ws_command_check(wsock, cmd: dict, expect: bool) -> None:
            """Execute a command and increment failures if necessary."""

            nonlocal fails
            status, _ = await ws_command_dict(wsock, cmd, expect)
            fails += int(not status)

        async def help_test():
            """Send some commands to the server."""

            nonlocal fails
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, close_timeout=1) as websocket:
                time.sleep(0.1)

                # test invalid json
                status, _ = await ws_command(
                    websocket, "{'command': 'help'}", False
                )
                fails += int(not status)

                # test valid json
                await ws_command_check(websocket, {"command": "help"}, True)

                # test udp client commands
                data = {}
                cmd = {"command": "udp", "data": data}
                await ws_command_check(websocket, cmd, False)
                data["operation"] = "asdf"
                await ws_command_check(websocket, cmd, False)
                data["operation"] = "list"
                await ws_command_check(websocket, cmd, True)

                # add a client
                data["operation"] = "add"
                await ws_command_check(websocket, cmd, False)
                data["host"] = "localhost"
                data["port"] = 0
                await ws_command_check(websocket, cmd, True)
                del data["host"]
                del data["port"]

                # list the single client
                data["operation"] = "list"
                status, raw = await ws_command_dict(websocket, cmd, True)
                fails += int(not status)
                clients = json.loads(raw)
                for client in clients:
                    data["id"] = int(client)
                    await ws_command_check(websocket, cmd, True)
                data["id"] = -1
                await ws_command_check(websocket, cmd, False)

                # remove the clients
                data["operation"] = "remove"
                del data["id"]
                await ws_command_check(websocket, cmd, False)
                data["id"] = -1
                await ws_command_check(websocket, cmd, False)

                for client in clients:
                    data["id"] = int(client)
                    await ws_command_check(websocket, cmd, True)

        for _ in range(5):
            asyncio.get_event_loop().run_until_complete(help_test())

    assert fails == 0


def test_telemetry_server_stop_http():
    """Test that the server can shutdown from an http request."""

    port = get_free_tcp_port()
    server = TelemetryServer(
        0.01,
        0.10,
        0.25,
        app_id_basis=0.5,
        services=default_services(http=Service("http", Host("0.0.0.0", port))),
    )
    with server.booted():
        # get app id
        result = requests.get(server.get_base_url() + "id", timeout=1.0)
        assert result.status_code == requests.codes["ok"]
        app_id = int(result.text)

        # should fail, no 'app_id'
        result = requests.post(server.get_base_url() + "shutdown", timeout=1.0)
        assert not result.status_code == requests.codes["ok"]

        # should fail, 'app_id' incorrect
        result = requests.post(
            server.get_base_url() + "shutdown",
            data={"app_id": 1234},
            timeout=1.0,
        )
        assert not result.status_code == requests.codes["ok"]

        # should succeed, 'app_id' correct
        result = requests.post(
            server.get_base_url() + "shutdown",
            data={"app_id": app_id},
            timeout=1.0,
        )
        assert result.status_code == requests.codes["ok"]
