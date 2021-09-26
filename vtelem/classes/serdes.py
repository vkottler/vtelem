"""
vtelem - A module exposing a base for implementing a class that can be encoded
         to JSON and decoded from JSON.
"""

# built-in
from json import dump, load, JSONEncoder, JSONDecoder
from io import StringIO
from typing import Dict, TextIO, Type, Union

DEFAULT_INDENT = 2
ObjectData = Dict[Union[int, str], Union[float, int, str, bool, None]]


class SerializableEncoder(JSONEncoder):
    """A simple encoder for the serializable base class."""

    def default(self, o) -> dict:
        """Encoder an object with an already-serializable 'data' attribute."""

        assert hasattr(o, "data")
        return o.data


class Serializable:
    """A class impementing a simple serialization interface (using JSON)."""

    def __init__(
        self,
        data: ObjectData = None,
        encoder: Type[JSONEncoder] = SerializableEncoder,
        decoder: Type[JSONDecoder] = JSONDecoder,
    ) -> None:
        """Construct a new serializable object."""

        if data is None:
            data = {}
        self.data = data
        self.encoder = encoder
        self.decoder = decoder
        self.init(self.data)

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

        dump(self, stream, indent=indent, sort_keys=True, cls=self.encoder)

    def json_str(self, indent: int = None) -> str:
        """Encode this object as a JSON String."""

        stream = StringIO()
        self.json(stream, indent)
        result = stream.getvalue()
        stream.close()
        return result

    def load(self, stream: TextIO) -> "Serializable":
        """Create a serializable from a text stream loaded as JSON."""

        data: ObjectData = load(stream, cls=self.decoder)
        return Serializable(data, self.encoder, self.decoder)

    def load_str(self, data: str) -> "Serializable":
        """Create a serializable from a String loaded as JSON."""

        stream = StringIO(data)
        result = self.load(stream)
        stream.close()
        return result
