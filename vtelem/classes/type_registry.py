
"""
vtelem - Contains a class for managing known type primitives.
"""

# built-in
from collections import defaultdict
import json
from typing import Tuple, Optional, Dict, List
import threading

# internal
from vtelem.enums.primitive import Primitive, PrimitiveEncoder, get_name


class TypeRegistry:
    """
    A class for managing types that can be registered and referenced by a
    name and an integer identifier.
    """

    def __init__(self, initial_types: List[Tuple[str, Primitive]] = None):
        """ Construct a new type registry, optionally add initial types. """

        self.data: Dict[str, dict] = {}
        types: Dict[int, Optional[Primitive]] = defaultdict(lambda: None)
        mappings: Dict[str, Optional[int]] = defaultdict(lambda: None)
        self.data["types"] = types
        self.data["mappings"] = mappings

        self.curr_id = 0
        self.lock = threading.RLock()

        # optionally register a set of initial types
        if initial_types is not None:
            for elem in initial_types:
                self.add(elem[0], elem[1])

    def get_type(self, type_id: int) -> Optional[Primitive]:
        """ Obtain a type's data by its integer identifier. """

        with self.lock:
            result = self.data["types"][type_id]
        return result

    def get_id(self, name: str) -> Optional[int]:
        """
        Determine the integer identifier for a named type, if it can be found.
        """

        with self.lock:
            result = self.data["mappings"][name]
        return result

    def add(self, name: str, data: Primitive) -> Tuple[bool, int]:
        """
        Register a named type, rejects duplicate names. Returns status
        of success and the integer identifier associated with this type.
        """

        with self.lock:
            if self.get_id(name) is not None:
                result = (False, -1)
            else:
                self.data["types"][self.curr_id] = data
                self.data["mappings"][name] = self.curr_id
                result = (True, self.curr_id)
                self.curr_id += 1

        return result

    def describe(self, indented: bool = False) -> str:
        """ Obtain a JSON String of the registry's current state. """

        indent = 4 if indented else None
        with self.lock:
            result = json.dumps(self.data, indent=indent, cls=PrimitiveEncoder,
                                sort_keys=True)
        return result


def get_default() -> TypeRegistry:
    """
    Get the default type registry, with the known primitive types
    pre-registered.
    """

    return TypeRegistry([(get_name(prim), prim) for prim in Primitive])
