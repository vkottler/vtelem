
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
from .stream_writer import StreamWriter
from .telemetry_environment import TelemetryEnvironment
from .time_keeper import TimeKeeper


class TelemetryServer(HttpDaemon):
    """ TODO """

    def __init__(self, tick_length: float, telem_rate: float,
                 address: Tuple[str, int] = None,
                 metrics_rate: float = None) -> None:
        """ TODO """

        self.daemons = DaemonManager()
        self.time_keeper = TimeKeeper("time", tick_length)
        assert self.daemons.add_daemon(self.time_keeper)
        # dynamically build MTU
        mtu = 1024
        self.env = TelemetryEnvironment(mtu, self.time_keeper.get_time(),
                                        metrics_rate)
        self.time_keeper.add_slave(self.env)

        # add the telemetry daemon
        assert self.daemons.add_daemon(Daemon("telemetry",
                                              self.env.dispatch_now,
                                              telem_rate,
                                              self.time_keeper.sleep, None,
                                              None, self.env))

        # add the telemetry-stream writer
        assert self.daemons.add_daemon(StreamWriter("stream",
                                                    self.env.frame_queue))

        # add the http daemon
        super().__init__("http", address, SimpleHTTPRequestHandler, self.env,
                         self.time_keeper)

    def scale_speed(self, scalar: float) -> None:
        """ TODO """

        assert self.daemons.perform_all(DaemonOperation.PAUSE)
        self.time_keeper.scale(scalar)
        assert self.daemons.perform_all(DaemonOperation.UNPAUSE)
