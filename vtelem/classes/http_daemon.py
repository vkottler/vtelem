"""
vtelem - Exposes a base class for building http services that can be managed
         as daemons.
"""

# built-in
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
    SimpleHTTPRequestHandler,
)
import logging
from typing import Type, Tuple

# internal
from .daemon_base import DaemonBase, DaemonState, MainThread
from .http_request_mapper import HttpRequestMapper, RequestHandle
from .service_registry import ServiceRegistry
from .telemetry_environment import TelemetryEnvironment
from .time_keeper import TimeKeeper

LOG = logging.getLogger(__name__)


class HttpDaemon(DaemonBase):
    """Allows daemonic management of an http server."""

    def __init__(
        self,
        name: str,
        address: Tuple[str, int] = None,
        handler_class: Type[BaseHTTPRequestHandler] = None,
        env: TelemetryEnvironment = None,
        time_keeper: TimeKeeper = None,
    ):
        """
        Construct a new HTTP daemon, which is a wrapper for the built-in
        server.
        """

        # listen on all interfaces, on an arbitrary port by default
        if address is None:
            address = ("0.0.0.0", 0)

        if handler_class is None:
            handler_class = SimpleHTTPRequestHandler

        super().__init__(name, env, time_keeper)
        self.server = ThreadingHTTPServer(address, handler_class)
        self.server.mapper = HttpRequestMapper()  # type: ignore
        host = self.server.server_address
        LOG.info("'%s' daemon bound to %s:%d", self.name, host[0], host[1])
        self.closed = False

        def stop_injector() -> None:
            """Signal the server to stop."""
            self.server.shutdown()

        self.function["inject_stop"] = stop_injector

    def get_base_url(self) -> str:
        """Get this server's root url as a String."""

        return "http://{}:{}/".format(
            self.server.server_address[0], self.server.server_address[1]
        )

    def add_handler(
        self,
        request_type: str,
        path: str,
        handle: RequestHandle,
        description: str = "no description",
        data: dict = None,
        response_type: str = "application/json",
    ) -> None:
        """Add a handler for a specific request-type and path."""

        mapper: HttpRequestMapper
        mapper = self.server.mapper  # type: ignore
        return mapper.add_handler(
            request_type, path, handle, description, data, response_type
        )

    def close(self) -> bool:
        """Close the server and clean up its resources."""

        with self.lock:
            if self.get_state() != DaemonState.IDLE or self.closed:
                return False
            self.closed = True

        self.server.server_close()
        return True

    def serve(self, *args, main_thread: MainThread = None, **kwargs) -> int:
        """
        Run this daemon with an optionally-provided main-thread function.
        Stops serving and closes server resources when the main-thread
        function returns.
        """

        result = super().serve(*args, main_thread=main_thread, **kwargs)
        assert self.close()
        return result

    def run(self, *_, **kwargs) -> None:
        """Serve traffic."""

        if not self.closed:
            if "first_start" in kwargs and "service_registry" in kwargs:
                first_start: bool = kwargs["first_start"]
                service_registry: ServiceRegistry = kwargs["service_registry"]
                if first_start:
                    service_registry.add(
                        self.name, [self.server.server_address]
                    )
            self.server.serve_forever(0.1)
