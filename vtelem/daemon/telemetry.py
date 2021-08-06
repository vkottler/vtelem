"""
vtelem - Exposes daemonic capabilities for telemetry.
"""

# built-in
from typing import List

# internal
from vtelem.channel import Channel
from vtelem.classes.time_keeper import TimeKeeper
from vtelem.classes.user_enum import UserEnum
from vtelem.daemon.synchronous import Daemon
from vtelem.telemetry.environment import TelemetryEnvironment


class TelemetryDaemon(TelemetryEnvironment, Daemon):
    """Wraps the telemetry-environment capability into a runtime daemon."""

    def __init__(
        self,
        name: str,
        mtu: int,
        rate: float,
        time_keeper: TimeKeeper,
        metrics_rate: float = None,
        initial_channels: List[Channel] = None,
        initial_enums: List[UserEnum] = None,
        app_id_basis: float = None,
        use_crc: bool = True,
    ) -> None:
        """Construct a new telemetry daemon."""

        TelemetryEnvironment.__init__(
            self,
            mtu,
            time_keeper.get_time(),
            metrics_rate,
            initial_channels,
            initial_enums,
            app_id_basis,
            use_crc,
        )
        Daemon.__init__(
            self, name, self.dispatch_now, rate, None, None, self, time_keeper
        )
