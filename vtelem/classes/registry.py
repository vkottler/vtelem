"""
vtelem - A generic registrar implementation.
"""

# built-in
from collections import defaultdict
import json
from typing import TypeVar, Generic, Tuple, Optional, Dict, List, Any
import threading

TYP = TypeVar("TYP")


class Registry(Generic[TYP]):
    """A base class for building type-specific registries."""

    def __init__(
        self, type_name: str, initial_data: List[Tuple[str, TYP]] = None
    ) -> None:
        """
        Construct a new registry of a provided type, optionally add initial
        elements.
        """

        self.type_name = type_name
        self.data: Dict[str, dict] = {}
        custom: Dict[int, Optional[TYP]] = defaultdict(lambda: None)
        mappings: Dict[str, Optional[int]] = defaultdict(lambda: None)
        self.data[self.type_name] = custom
        self.data["mappings"] = mappings

        self.curr_id: int = 0
        self.lock = threading.RLock()

        # optionally register a set of initial items
        if initial_data is not None:
            for item in initial_data:
                self.add(item[0], item[1])

    def count(self) -> int:
        """Get a count of the number of elements in this registry."""

        return self.curr_id

    def get_item(self, item_id: int) -> Optional[TYP]:
        """Obtain an item's data by its integer identifier."""

        with self.lock:
            result = self.data[self.type_name][item_id]
        return result

    def get_id(self, name: str) -> Optional[int]:
        """
        Determine the integer identifier for a named type, if it can be found.
        """

        with self.lock:
            result = self.data["mappings"][name]
        return result

    def add(self, name: str, data: TYP) -> Tuple[bool, int]:
        """
        Register a named item, rejects duplicate names. Returns status
        of success and the integer identifier associated with this item.
        """

        with self.lock:
            if self.get_id(name) is not None:
                result = (False, -1)
            else:
                self.data[self.type_name][self.curr_id] = data
                self.data["mappings"][name] = self.curr_id
                result = (True, self.curr_id)
                self.curr_id += 1

        return result

    def describe(self, indented: bool = False) -> str:
        """A default implementation."""

        return self.describe_raw(indented)

    def describe_raw(self, indented: bool = False, cls: Any = None) -> str:
        """Obtain a JSON String of the registry's current state."""

        indent = 4 if indented else None
        with self.lock:
            result = json.dumps(
                self.data, indent=indent, cls=cls, sort_keys=True
            )
        return result
