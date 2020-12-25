
"""
vtelem - Exposes daemonic capabilities for telemetry.
"""

# built-in
from typing import List

# internal
from vtelem.names import class_to_snake
from .channel import Channel
from .telemetry_environment import TelemetryEnvironment
from .time_keeper import TimeKeeper
from .daemon import Daemon, DaemonState
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

        # add daemon-state telemetry
        self.add_from_enum(DaemonState)
        self.add_enum_metric("daemon", class_to_snake(DaemonState), True)

        def set_daemon_state_channel(_: DaemonState,
                                     curr_state: DaemonState,
                                     time: float) -> None:
            """ Callback for daemon-state change. """
            self.set_enum_metric("daemon", curr_state.name.lower(), time)

        # overrun function
        # metrics function

        # initialize the daemon
        Daemon.__init__(self, self.dispatch_now, rate, self.get_time,
                        time_keeper.sleep, "telemetry", None, None,
                        set_daemon_state_channel)

        # set initial daemon state
        self.set_enum_metric("daemon", self.get_state_str(),
                             time_keeper.time())
