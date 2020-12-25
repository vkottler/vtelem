
"""
vtelem - Exposes daemonic capabilities for telemetry.
"""

# built-in
from typing import List

# internal
from .channel import Channel
from .telemetry_environment import TelemetryEnvironment
from .time_keeper import TimeKeeper
from .daemon import Daemon
from .user_enum import UserEnum


class TelemetryDaemon(TelemetryEnvironment, Daemon):
    """ Wraps the telemetry-environment capability into a runtime daemon. """

    def __init__(self, mtu: int, rate: float, time_keeper: TimeKeeper,
                 metrics_rate: float = None,
                 initial_channels: List[Channel] = None,
                 initial_enums: List[UserEnum] = None) -> None:
        """ Construct a new telemetry daemon. """

        TelemetryEnvironment.__init__(self, mtu, time_keeper.time(),
                                      metrics_rate, initial_channels,
                                      initial_enums)
        time_keeper.add_slave(self)

        # overrun function
        # metrics function

        # initialize the daemon
        Daemon.__init__(self, "telemetry", self.dispatch_now, rate,
                        self.get_time, time_keeper.sleep, None, None, self)
