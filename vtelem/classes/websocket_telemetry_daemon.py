
"""
vtelem - An interface for managing websocket servers that serve telemetry data.
"""

# built-in
import logging
from typing import Any, Tuple

# internal
from .stream_writer import StreamWriter
from .telemetry_environment import TelemetryEnvironment
from .websocket_daemon import WebsocketDaemon

LOG = logging.getLogger(__name__)


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

            laddr = websocket.local_address
            raddr = websocket.remote_address
            conn = "opened"
            fstr = "telemetry connection ('%s') %s '%s:%d' -> '%s:%d'"
            LOG.info(fstr, path, conn, laddr[0], laddr[1], raddr[0], raddr[1])

            while websocket.open:
                pass

            # add the socket to the stream-writer, while loop on the connection
            # being open (we need to handle close signals somehow), once the
            # connection gets closed remove us from the stream-writer
            # ('finally' clause?)
            print(websocket)
            print(path)
            print(writer)

            conn = "closed"
            LOG.info(fstr, path, conn, laddr[0], laddr[1], raddr[0], raddr[1])

        super().__init__(name, None, address, env, time_keeper, telem_handle)
