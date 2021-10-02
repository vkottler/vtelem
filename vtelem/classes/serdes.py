"""
vtelem - A module exposing a base for implementing a class that can be encoded
         to JSON and decoded from JSON.
"""

# built-in
from json import dump, load, JSONEncoder, JSONDecoder
import logging
from io import StringIO
from typing import Dict, NamedTuple, List, Optional, TextIO, Type, Union

# third-party
from cerberus import Validator

# internal
from vtelem.schema.manager import SchemaManager

LOG = logging.getLogger(__name__)
DEFAULT_INDENT = 2

# See RFC 8259.
ObjectKey = Union[int, str]
ObjectElement = Union[float, int, str, bool, None]
ObjectMap = Dict[ObjectKey, ObjectElement]
ObjectData = Dict[
    ObjectKey,
    Union[ObjectElement, List[ObjectElement], ObjectMap],
]


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
    ) -> None:
        """Construct a new serializable object."""

        if data is None:
            data = {}
        self.data = data

        if params is None:
            params = SerializableParams()
        self.params = params

        self.log = log
        self.init(self.data)
        self.valid = self.validate()

    @staticmethod
    def int_keys(data: ObjectMap) -> ObjectMap:
        """Coerce keys in a map to integer."""

        return {int(key): value for key, value in data.items()}

    @classmethod
    def schema(cls, manager: SchemaManager) -> Validator:
        """Get the schema for this class from a schema manager."""

        return manager.get(cls)

    def validate(self, log: bool = True) -> bool:
        """
        Attempt to validate this object's data against a schema, if one was
        provided at initialization.
        """

        result = True
        if self.params.schema is not None:
            result = self.params.schema.validate(self.data)
            if not result and log:
                self.log.error(
                    "Schema validation error(s) for an instance of '%s': %s",
                    self.__class__.__name__,
                    self.params.schema.errors,
                )
                self.log.error("data: %s", self.data)
                self.log.error("schema: %s", self.params.schema.schema)
        return result

    def __eq__(self, other) -> bool:
        """Check if two serializables are equivalent."""

        result = False
        if hasattr(other, "data"):
            result = self.data == other.data
        return result

    def init(self, data: ObjectData) -> None:
        """
        Can be implemented to set up a serializable from some initial data.
        """

    def json(self, stream: TextIO, indent: int = None) -> None:
        """Encode this object as JSON to the provided stream."""

        dump(
            self,
            stream,
            indent=indent,
            sort_keys=True,
            cls=self.params.encoder,
        )

    def json_str(self, indent: int = None) -> str:
        """Encode this object as a JSON String."""

        with StringIO() as stream:
            self.json(stream, indent)
            return stream.getvalue()

    def load(self, stream: TextIO) -> "Serializable":
        """Create a serializable from a text stream loaded as JSON."""

        data: ObjectData = load(stream, cls=self.params.decoder)
        return self.__class__(data, self.params)

    def load_str(self, data: str) -> "Serializable":
        """Create a serializable from a String loaded as JSON."""

        with StringIO(data) as stream:
            return self.load(stream)
