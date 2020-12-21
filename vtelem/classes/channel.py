
"""
vtelem - A storage class that emits on an interval.
"""

# built-in
from typing import Any, Optional

# internal
from vtelem.enums.primitive import Primitive
from .type_primitive import TypePrimitive
from .event_queue import EventQueue


class Channel(TypePrimitive):
    """
    A storage class for a primitive that can be emitted (to a caller) at a
    desired interval. It can also emit events to a queue when the value
    changes.
    """

    def __init__(self, name: str, instance: Primitive, rate: float,
                 event_queue: EventQueue = None) -> None:
        """
        Construct a new channel of a provided primitive type that should be
        emitted at a specified rate.
        """

        # provide the event queue callback if it was provided, otherwise
        # nothing
        changed_cb = None
        if event_queue is not None:
            changed_cb = event_queue.enqueue

        super().__init__(instance, changed_cb)
        self.name = name
        self.rate = rate
        self.last_emitted: float = float()

    def emit(self, time: float) -> Optional[Any]:
        """
        If the provided time indicates that this channel should be emitted
        again, return the current value. Otherwise return nothing.
        """

        result = None
        with self.lock:
            if time >= (self.last_emitted + self.rate):
                result = self.get()
                self.last_emitted = time
        return result
