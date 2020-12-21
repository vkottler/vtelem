
"""
vtelem - A definition of the supported primitive types for this library.
"""

# built-in
from copy import copy
from enum import Enum
from json import JSONEncoder
from typing import Any


def build_primitive(fmt: str, inst: type, size: int, name: str) -> dict:
    """ Build a primitive dictionary from data. """

    return {"format": fmt, "type": inst, "size": size, "name": name}


class Primitive(Enum):
    """
    An enumeration containing the supported primitive types and their 'struct'
    format specifier.
    """

    BOOL = build_primitive("?", bool, 1, "boolean")
    INT8 = build_primitive("b", int, 1, "int8")
    UINT8 = build_primitive("B", int, 1, "uint8")
    INT16 = build_primitive("h", int, 2, "int16")
    UINT16 = build_primitive("H", int, 2, "uint16")
    INT32 = build_primitive("i", int, 4, "int32")
    UINT32 = build_primitive("I", int, 4, "uint32")
    INT64 = build_primitive("q", int, 8, "int64")
    UINT64 = build_primitive("Q", int, 8, "uint64")
    FLOAT = build_primitive("f", float, 4, "float")
    DOUBLE = build_primitive("d", float, 8, "double")


class PrimitiveEncoder(JSONEncoder):
    """ A JSON encoder for a primitive enum. """

    def default(self, o) -> dict:
        """ Implement serialization for the primitive enum value. """

        assert isinstance(o, Primitive)
        result = copy(o.value)
        result["type"] = str(result["type"])
        return result


def get_name(inst: Primitive) -> str:
    """ Get a primitive's canonical name. """

    return inst.value["name"]


def get_fstring(inst: Primitive) -> str:
    """ Get the 'struct' format specifier for a primitive. """

    return inst.value["format"]


def get_size(inst: Primitive) -> int:
    """ Get the size of a primitive. """

    return inst.value["size"]


def default_val(inst: Primitive) -> Any:
    """ Get the default value for a specific primitive. """

    return inst.value["type"]()
