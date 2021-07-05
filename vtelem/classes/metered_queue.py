"""
vtelem - Allows queues to publish telemetry metrics.
"""

# built-in
from queue import Queue
from typing import Any

# internal
from vtelem.enums.primitive import Primitive


class MeteredQueue(Queue):
    """
    Extends the standard queue so that metrics can be tracked in a
    telemetry-capable environment.
    """

    def __init__(self, name: str, env: Any, maxsize: int = 0) -> None:
        """Construct a new queue that publishes metrics to an environment."""

        super().__init__(maxsize)
        self.env = env
        self.name = "{}_queue".format(name)
        initial = (0, self.env.get_time())
        self.env.add_metric(
            "{}.elements".format(self.name), Primitive.UINT16, False, initial
        )
        self.env.add_metric(
            "{}.total_enqueued".format(self.name),
            Primitive.UINT32,
            False,
            initial,
        )
        self.env.add_metric(
            "{}.total_dequeued".format(self.name),
            Primitive.UINT32,
            False,
            initial,
        )

    def get(self, block: bool = True, timeout: float = None) -> Any:
        """Dequeue an element."""

        result = super().get(block, timeout)
        time = self.env.get_time()
        self.env.metric_add("{}.elements".format(self.name), -1, time)
        self.env.metric_add("{}.total_dequeued".format(self.name), 1, time)
        return result

    def put(
        self, item: Any, block: bool = True, timeout: float = None
    ) -> None:
        """Enqueue an element."""

        super().put(item, block, timeout)
        time = self.env.get_time()
        self.env.metric_add("{}.elements".format(self.name), 1, time)
        self.env.metric_add("{}.total_enqueued".format(self.name), 1, time)
