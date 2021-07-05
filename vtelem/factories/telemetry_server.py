"""
vtelem - A module for creating functions based on a telemetry server instance.
"""

# built-in
from http.server import BaseHTTPRequestHandler
import json
from typing import Any, Tuple

# internal
from vtelem.classes.command_queue_daemon import CommandQueueDaemon
from vtelem.classes.telemetry_daemon import TelemetryDaemon


def register_http_handlers(
    server: Any, telem: TelemetryDaemon, cmd: CommandQueueDaemon
) -> None:
    """Register http request handlers to a telemetry server."""

    def app_id(_: BaseHTTPRequestHandler, __: dict) -> Tuple[bool, str]:
        """Provide the application identifier."""
        return True, str(telem.app_id.get())

    def shutdown(_: BaseHTTPRequestHandler, data: dict) -> Tuple[bool, str]:
        """
        Attemp to shut this server down, required the correct application
        identifier.
        """

        our_id = telem.app_id
        provided_id = data["app_id"]
        if provided_id is None:
            return False, "no 'app_id' argument provided"
        provided_id = provided_id[0]
        if our_id.get() != int(provided_id):
            msg = "'app_id' mismatch, expected '{}' got '{}'"
            return False, msg.format(our_id.get(), int(provided_id))
        server.stop_all()
        return True, "success"

    def get_types(_: BaseHTTPRequestHandler, data: dict) -> Tuple[bool, str]:
        """Return the type-registry contents as JSON."""
        indented = data["indent"] is not None
        return True, telem.type_registry.describe(indented)

    def get_registries(
        _: BaseHTTPRequestHandler, data: dict
    ) -> Tuple[bool, str]:
        """Return all registry data as JSON."""
        indented = data["indent"] is not None
        rdata = {}
        for key, registry in telem.registries.items():
            rdata[key] = json.loads(registry.describe())
        return True, json.dumps(rdata, indent=(4 if indented else None))

    def run_command(_: BaseHTTPRequestHandler, data: dict) -> Tuple[bool, str]:
        """Execute a command through the command-queue daemon."""

        if "command" not in data:
            return False, "no 'command' specified. (try 'help')"

        # collapse list items into single values
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = value[0]

        # move additional arguments to the "data" key
        if "data" not in data:
            data["data"] = {}
            for key, value in data.items():
                if key not in ["command", "data"]:
                    data["data"][key] = value

        return cmd.execute(data)

    # add request handlers
    server.add_handler(
        "GET",
        "id",
        app_id,
        ("get this telemetry instance's " + "application identifier"),
    )
    server.add_handler(
        "GET", "types", get_types, "get the numerical mappings for known types"
    )
    server.add_handler(
        "GET", "registries", get_registries, "get registry data"
    )
    server.add_handler("POST", "shutdown", shutdown, "shutdown the server")

    server.add_handler(
        "GET", "command", run_command, "send a command to the server"
    )
    server.add_handler(
        "POST", "command", run_command, "send a command to the server"
    )
