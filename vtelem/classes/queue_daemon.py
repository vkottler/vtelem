
"""
vtelem - Uses daemon machinery to make servicing queues in threads simple.
"""

# built-in
from queue import Queue
from typing import Callable

# internal
from .daemon_base import DaemonBase


class QueueDaemon(DaemonBase):
    """ Implements a daemon thread for servicing queues. """

    def __init__(self, name: str, input_stream: Queue,
                 elem_handle: Callable) -> None:
        """ Construct a new queue daemon. """

        super().__init__(name)
        self.queue = input_stream
        self.handle = elem_handle

        def stop_injector() -> None:
            """ Put a None into the queue as the signal for stopping. """
            self.queue.put(None)

        self.function["inject_stop"] = stop_injector

    def run(self, *_, **__) -> None:
        """ Continue servicing the queue until None is de-queued. """

        elem = self.queue.get()
        while elem is not None:
            self.handle(elem)
            self.queue.task_done()
            elem = self.queue.get()
        self.queue.task_done()
