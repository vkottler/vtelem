
"""
vtelem - A queue that stores change events that can be completely drained on
         command.
"""

# built-in
from queue import Queue
import threading
from typing import Any, List, Tuple


class EventQueue:
    """ A queue for storing primitive-data change events. """

    def __init__(self) -> None:
        """ Construct an empty queue. """

        self.queue: Queue = Queue()
        self.lock = threading.Lock()

    def enqueue(self, prev: Tuple[Any, float],
                curr: Tuple[Any, float]) -> None:
        """ Put an event into the queue. """

        self.queue.put((prev, curr))

    def consume(self) -> List[Tuple[Tuple[Any, float], Tuple[Any, float]]]:
        """ Get all of the current events in the queue as a list. """

        result = []
        with self.lock:
            while not self.queue.empty():
                result.append(self.queue.get())
        return result
