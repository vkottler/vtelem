"""
vtelem - A module for using event loops as daemons.
"""

# built-in
import asyncio
from threading import Semaphore
from typing import Any

# internal
from vtelem.daemon import DaemonBase
from vtelem.telemetry.environment import TelemetryEnvironment


class EventLoopDaemon(DaemonBase):
    """A class for wrapping asyncio event loops with daemonic behavior."""

    def __init__(
        self,
        name: str,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
    ) -> None:
        """Construct a new event-loop daemon."""

        super().__init__(name, env, time_keeper)
        self.eloop = asyncio.new_event_loop()
        self.wait_count = 0
        self.wait_poster = Semaphore(0)

        def event_loop_stopper() -> None:
            """
            A function for stopping the event loop from an arbitrary thread.
            """

            # determine how many tasks have expressed pending status
            with self.lock:
                waits = self.wait_count

            # signal active tasks to cancel
            tasks = asyncio.all_tasks(loop=self.eloop)
            for task in tasks:
                task.cancel()

            # schedule event-loop shutdown, if we leave un-finished work behind
            # it's better than hanging
            self.eloop.call_soon_threadsafe(self.eloop.stop)

            # decrement the semaphore the required number of times
            waited = 0
            for _ in range(waits):
                sig = self.wait_poster
                if sig.acquire(True, 2):  # pylint:disable=consider-using-with
                    waited += 1

            assert waited == waits
            with self.lock:
                self.wait_count -= waits

        self.function["inject_stop"] = event_loop_stopper

    def run(self, *args, **kwargs) -> None:
        """Runs this daemon's thread, until stop is requested."""

        asyncio.set_event_loop(self.eloop)
        try:
            self.function["run_init"](*args, **kwargs)
        except KeyError:
            pass
        self.eloop.run_forever()
