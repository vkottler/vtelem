"""
vtelem - A module exposing a base for implementing a class that can be encoded
         to JSON and decoded from JSON.
"""

# built-in
from io import StringIO
from json import JSONDecoder, JSONEncoder, dump, load
import logging
from typing import List, NamedTuple, Optional, TextIO, Type, cast

# third-party
from cerberus import Validator

# internal
from vtelem.names import class_to_snake
from vtelem.schema.manager import SchemaManager
from vtelem.types.serializable import ObjectData, ObjectKey, ObjectMap

LOG = logging.getLogger(__name__)
DEFAULT_INDENT = 2


class SerializableEncoder(JSONEncoder):
    """A simple encoder for the serializable base class."""

    def default(self, o) -> dict:
        """Encoder an object with an already-serializable 'data' attribute."""

        assert hasattr(o, "data")
        return o.data


class SerializableParams(NamedTuple):
    """Parameters that control the behavior of a serializable object."""

    encoder: Type[JSONEncoder] = SerializableEncoder
    decoder: Type[JSONDecoder] = JSONDecoder
    schema: Optional[Validator] = None


class Serializable:
    """A class impementing a simple serialization interface (using JSON)."""

    def __init__(
        self,
        data: ObjectData = None,
        params: SerializableParams = None,
        log: logging.Logger = LOG,
        manager: SchemaManager = None,
    ) -> None:
        """Construct a new serializable object."""

        super().__init__()
        if data is None:
            data = {}
        self.data = data

        # Set a 'type' attribute so it's easier to keep track of what a given
        # serializable is actually supposed to be.
        if "type" not in self.data:
            self.data["type"] = class_to_snake(type(self))

        if params is None:
            params = SerializableParams()
        self.params = params
        self.manager: Optional[SchemaManager] = manager

        self.log = log
        self.init(self.data)
        self.valid = self.validate(manager=self.manager)

    @staticmethod
    def int_keys(data: ObjectMap) -> ObjectMap:
        """Coerce keys in a map to integer."""

        return {int(key): value for key, value in data.items()}

    @classmethod
    def schema(cls, manager: SchemaManager) -> Validator:
        """Get the schema for this class from a schema manager."""

        return manager.get(cls)

    def validate(
        self, log: bool = True, manager: SchemaManager = None
    ) -> bool:
        """
        Attempt to validate this object's data against a schema, if one was
        provided at initialization.
        """

        result = True

        # Use either the provided schema, or one sourced from a schema manager.
        schema = self.params.schema
        if schema is None and manager is not None:
            schema = manager.get(self.__class__)

        if schema is not None:
            result = schema.validate(self.data)
            if not result and log:
                self.log.error(
                    "Schema validation error(s) for an instance of '%s': %s",
                    self.__class__.__name__,
                    schema.errors,
                )
                self.log.error("data: %s", self.data)
                self.log.error("schema: %s", schema.schema)
        return result

    def __eq__(self, other) -> bool:
        """Check if two serializables are equivalent."""

        result = False
        if hasattr(other, "data"):
            result = self.data == other.data
        return result and isinstance(other, type(self))

    def init(self, data: ObjectData) -> None:
        """
        Can be implemented to set up a serializable from some initial data.
        """

    def json(self, stream: TextIO, indent: int = None, **dump_kwargs) -> None:
        """Encode this object as JSON to the provided stream."""

        dump(
            self,
            stream,
            indent=indent,
            sort_keys=True,
            cls=self.params.encoder,
            **dump_kwargs,
        )

    def json_str(self, indent: int = None, **dump_kwargs) -> str:
        """Encode this object as a JSON String."""

        with StringIO() as stream:
            self.json(stream, indent, **dump_kwargs)
            return stream.getvalue()

    def load(self, stream: TextIO, **load_kwargs) -> "Serializable":
        """Create a serializable from a text stream loaded as JSON."""

        data: ObjectData = load(stream, cls=self.params.decoder, **load_kwargs)
        return self.__class__(data, self.params)

    def load_str(self, data: str, **load_kwargs) -> "Serializable":
        """Create a serializable from a String loaded as JSON."""

        with StringIO(data) as stream:
            return self.load(stream, **load_kwargs)

    def coerce_int_keys(
        self, paths: List[ObjectKey], data: ObjectData = None
    ) -> None:
        """
        Coerce keys in a mapping at some path (from 'data' root) to integers.
        """

        data = self.data if data is None else data
        assert paths
        for i in range(len(paths) - 1):
            data = cast(ObjectData, data.get(paths[i], {}))

        to_convert = data.get(paths[-1], {})
        data[paths[-1]] = Serializable.int_keys(cast(ObjectMap, to_convert))

    @property
    def name(self) -> str:
        """Get the name of this object."""

        return cast(str, self.data.get("name", type(self).__name__))

    def __hash__(self) -> int:
        """Allow serializables to be hashable by name."""

        return hash(self.name)


def max_key(data: ObjectMap) -> int:
    """
    Get the highest integer-value key in a given map, or -1 if no integer keys
    are found.
    """

    result = -1
    for key in data:
        if isinstance(key, int) and key > result:
            result = key
    return result
