
"""
vtelem - TODO.
"""

# built-in
from http.server import SimpleHTTPRequestHandler
from typing import Tuple

# internal
from .daemon import Daemon
from .daemon_base import DaemonOperation
from .daemon_manager import DaemonManager
from .http_daemon import HttpDaemon
from .telemetry_environment import TelemetryEnvironment
from .time_keeper import TimeKeeper


class TelemetryServer(DaemonManager):
    """ TODO """

    def __init__(self, tick_length: float, telem_rate: float,
                 address: Tuple[str, int] = None,
                 metrics_rate: float = None) -> None:
        """ TODO """

        super().__init__()
        self.time_keeper = TimeKeeper("time_master", tick_length)
        assert self.add_daemon(self.time_keeper)
        # dynamically build MTU
        mtu = 1024
        self.env = TelemetryEnvironment(mtu, self.time_keeper.get_time(),
                                        metrics_rate)
        self.time_keeper.add_slave(self.env)

        # add the telemetry daemon
        assert self.add_daemon(Daemon("telemetry", self.env.dispatch_now,
                                      telem_rate, self.time_keeper.sleep, None,
                                      None, self.env))

        # add the telemetry-stream writer

        # add the http daemon
        assert self.add_daemon(HttpDaemon("http", address,
                                          SimpleHTTPRequestHandler, self.env,
                                          self.time_keeper))

    def scale_speed(self, scalar: float) -> None:
        """ TODO """

        assert self.perform_all(DaemonOperation.PAUSE)
        self.time_keeper.scale(scalar)
        assert self.perform_all(DaemonOperation.UNPAUSE)
