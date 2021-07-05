"""
vtelem - A storage class that emits on an interval.
"""

# built-in
from json import JSONEncoder
from typing import Any, Optional

# internal
from vtelem.enums.primitive import Primitive
from . import EventType
from .type_primitive import TypePrimitive
from .event_queue import EventQueue


class Channel(TypePrimitive):
    """
    A storage class for a primitive that can be emitted (to a caller) at a
    desired interval. It can also emit events to a queue when the value
    changes.
    """

    def __init__(
        self,
        name: str,
        instance: Primitive,
        rate: float,
        event_queue: EventQueue = None,
        commandable: bool = True,
    ) -> None:
        """
        Construct a new channel of a provided primitive type that should be
        emitted at a specified rate.
        """

        # provide the event queue callback if it was provided, otherwise
        # nothing
        changed_cb = None
        if event_queue is not None:

            def new_changed_cb(prev: EventType, curr: EventType) -> None:
                """Create a function specific to this channel."""
                assert event_queue is not None
                event_queue.enqueue(name, prev, curr)

            changed_cb = new_changed_cb

        super().__init__(instance, changed_cb)
        self.name = name
        self.rate = rate
        self.commandable = commandable
        self.last_emitted: float = float()

    def command(
        self, value: Any, time: float = None, add: bool = False
    ) -> bool:
        """Attempt to command this channel to a new value"""

        if not self.commandable:
            return False
        operation = self.add if add else self.set
        with self.lock:
            return operation(value, time)

    def set_rate(self, rate: float) -> None:
        """Set a channel's rate post-initialization."""

        with self.lock:
            self.rate = rate

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


class ChannelEncoder(JSONEncoder):
    """A JSON encoder for a primitive enum."""

    def default(self, o) -> dict:
        """Implement serialization for the primitive enum value."""

        assert isinstance(o, Channel)
        type_dict = {
            "name": o.type.value["name"],
            "signed": o.type.value["name"],
            "size": o.type.value["size"],
        }
        result = {
            "name": o.name,
            "rate": o.rate,
            "commandable": o.commandable,
            "type": type_dict,
        }
        return result
