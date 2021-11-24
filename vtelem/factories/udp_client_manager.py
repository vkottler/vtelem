"""
vtelem - A module for creating functions based on a udp-client-manager.
"""

# built-in
import json
from typing import Tuple

# internal
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.daemon.command_queue import CommandQueueDaemon
from vtelem.mtu import Host
from vtelem.types.command_queue_daemon import ResultCbType


def add_client(manager: UdpClientManager, data: dict) -> Tuple[bool, str]:
    """Attempt to add a new client."""

    if "host" not in data and "port" not in data:
        return False, "must provide 'host' and 'port'"

    result = manager.add_client(Host(data["host"], data["port"]))
    client_name = manager.client_name(result[0])
    client_str = f"{client_name[0]}:{client_name[1]}"
    msg = f"client '{result[0]}' ({client_str}) added with mtu '{result[1]}'"
    return True, msg


def remove_client(manager: UdpClientManager, data: dict) -> Tuple[bool, str]:
    """Attempt to remove a registered client."""

    with manager.lock:
        if "id" not in data:
            return False, "client identifier not provided"
        if data["id"] not in manager.clients:
            return False, f"unknown client identifier '{data['id']}'"
        manager.remove_client(data["id"])
    return True, f"client '{data['id']}' removed"


def list_client(manager: UdpClientManager, data: dict) -> Tuple[bool, str]:
    """Attempt to list registered clients."""

    with manager.lock:
        sock_ids = list(manager.clients.keys())
        if "id" in data:
            if data["id"] not in manager.clients:
                return False, f"unknown client identifier '{data['id']}'"
            sock_ids = [data["id"]]

        result = {}
        for sock_id in sock_ids:
            name = manager.client_name(sock_id)
            result[sock_id] = f"{name[0]}:{name[1]}"

    return True, json.dumps(result)


def create_udp_client_commander(
    manager: UdpClientManager,
    daemon: CommandQueueDaemon,
    result_cb: ResultCbType = None,
    command_name: str = "udp",
) -> None:
    """Register a handler to a command queue for a udp-client-manager."""

    commands = {
        "add": add_client,
        "remove": remove_client,
        "list": list_client,
    }

    def udp_commander(cmd: dict) -> Tuple[bool, str]:
        """Attempt to run a udp-client-manager command."""

        if "operation" not in cmd:
            return False, "no 'operation' specified"
        if cmd["operation"] not in commands:
            return False, f"'{cmd['operation']}' not supported"
        return commands[cmd["operation"]](manager, cmd)

    ops_str = ", ".join(f"'{val}'" for val in commands)
    daemon.register_consumer(
        command_name,
        udp_commander,
        result_cb,
        f"{ops_str} udp clients",
    )
