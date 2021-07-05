"""
vtelem - A queue that stores change events that can be completely drained on
         command.
"""

# built-in
from queue import Queue
import threading
from typing import List, Tuple

# internal
from . import EventType


class EventQueue:
    """A queue for storing primitive-data change events."""

    def __init__(self) -> None:
        """Construct an empty queue."""

        self.queue: Queue = Queue()
        self.lock = threading.Lock()

    def enqueue(self, channel: str, prev: EventType, curr: EventType) -> None:
        """Put an event into the queue."""

        self.queue.put((channel, prev, curr))

    def consume(self) -> List[Tuple[str, EventType, EventType]]:
        """Get all of the current events in the queue as a list."""

        result = []
        with self.lock:
            while not self.queue.empty():
                result.append(self.queue.get())
        return result
