
"""
vtelem - An interface for managing websocket servers that serve telemetry data.
"""

# built-in
from typing import Any, Tuple

# internal
from .stream_writer import StreamWriter
from .telemetry_environment import TelemetryEnvironment
from .websocket_daemon import WebsocketDaemon


class WebsocketTelemetryDaemon(WebsocketDaemon):
    """ A class for creating telemetry-serving websocket servers. """

    def __init__(self, name: str, writer: StreamWriter,
                 address: Tuple[str, int] = None,
                 env: TelemetryEnvironment = None,
                 time_keeper: Any = None) -> None:
        """ Construct a new, telemetry-serving websocket server. """

        async def telem_handle(websocket, path) -> None:
            """
            Write telemetry to this connection, for as long as it's connected.
            """

            # add the socket to the stream-writer, while loop on the connection
            # being open (we need to handle close signals somehow), once the
            # connection gets closed remove us from the stream-writer
            # ('finally' clause?)
            print(websocket)
            print(path)
            print(writer)

        super().__init__(name, None, address, env, time_keeper, telem_handle)
