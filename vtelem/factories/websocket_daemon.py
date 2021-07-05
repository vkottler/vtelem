"""
vtelem - A module for creating different types of websocket daemons.
"""

# built-in
import json
from typing import Tuple

# internal
from vtelem.classes.command_queue_daemon import CommandQueueDaemon
from vtelem.classes.websocket_daemon import WebsocketDaemon
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.classes.time_keeper import TimeKeeper


def commandable_websocket_daemon(
    name: str,
    daemon: CommandQueueDaemon,
    address: Tuple[str, int] = None,
    env: TelemetryEnvironment = None,
    keeper: TimeKeeper = None,
) -> WebsocketDaemon:
    """
    Construct a daemon that forwards commands to the telemetry environment.
    """

    async def command_handler(websocket, message, _):
        """
        Interpret a websocket message as a command, execute it and send back
        the result.
        """

        result = {"success": False, "message": "Command result not known."}

        # build command, result callback
        try:
            cmd_result = daemon.execute(json.loads(message))
            result["success"] = cmd_result[0]
            result["message"] = cmd_result[1]
        except json.decoder.JSONDecodeError as exc:
            result["message"] = str(exc)

        await websocket.send(json.dumps(result))

    return WebsocketDaemon(name, command_handler, address, env, keeper)
