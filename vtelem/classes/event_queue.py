"""
vtelem - A queue that stores change events that can be completely drained on
         command.
"""

# built-in
from queue import Full, Queue
import threading
from typing import List, Tuple

# internal
from . import EventType
from .metered_queue import create


class EventQueue:
    """A queue for storing primitive-data change events."""

    def __init__(self) -> None:
        """Construct an empty queue."""

        self.queue: Queue = create()
        self.lock = threading.Lock()

    def enqueue(self, channel: str, prev: EventType, curr: EventType) -> bool:
        """Put an event into the queue."""

        try:
            self.queue.put_nowait((channel, prev, curr))
            return True
        except Full:
            return False

    def consume(self) -> List[Tuple[str, EventType, EventType]]:
        """Get all of the current events in the queue as a list."""

        result = []
        with self.lock:
            while not self.queue.empty():
                result.append(self.queue.get())
        return result
