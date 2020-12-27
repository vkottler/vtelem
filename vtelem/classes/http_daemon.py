
"""
vtelem - Exposes a base class for building http services that can be managed
         as daemons.
"""

# built-in
from http.server import (
    BaseHTTPRequestHandler, ThreadingHTTPServer, SimpleHTTPRequestHandler
)
from typing import Type, Callable, Tuple

# internal
from .daemon_base import DaemonBase, DaemonState
from .telemetry_environment import TelemetryEnvironment


class HttpDaemon(DaemonBase):
    """ Allows daemonic management of an http server. """

    def __init__(self, name: str, address: Tuple[str, int] = None,
                 handler_class: Type[BaseHTTPRequestHandler] = None,
                 get_time_fn: Callable = None,
                 env: TelemetryEnvironment = None):
        """
        Construct a new HTTP daemon, which is a wrapper for the built-in
        server.
        """

        # listen on all interfaces, on an arbitrary port by default
        if address is None:
            address = ("0.0.0.0", 0)

        if handler_class is None:
            handler_class = SimpleHTTPRequestHandler

        super().__init__(name, get_time_fn, env)
        self.server = ThreadingHTTPServer(address, handler_class)
        self.closed = False

        def stop_injector() -> None:
            """ Signal the server to stop. """
            self.server.shutdown()

        self.function["inject_stop"] = stop_injector

    def get_base_url(self) -> str:
        """ Get this server's root url as a String. """

        return "http://{}:{}/".format(self.server.server_address[0],
                                      self.server.server_address[1])

    def close(self) -> bool:
        """ Close the server and clean up its resources. """

        with self.lock:
            if self.get_state() != DaemonState.IDLE or self.closed:
                return False
            self.closed = True

        self.server.server_close()
        return True

    def run(self, *_, **__) -> None:
        """ Serve traffic. """

        if not self.closed:
            self.server.serve_forever(0.1)
