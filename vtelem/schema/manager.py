"""
vtelem - A module for managing schemas.
"""

# built-in
from pathlib import Path
from typing import Type

# third-party
from cerberus import Validator
from datazen.paths import get_file_name

# internal
from vtelem.schema import SchemaMap, load_schema, load_schema_dir


class SchemaManager:
    """
    A class for keeping track of loaded schemas at runtime, and providing
    simple lookup mechanisms.
    """

    def __init__(self, initial: SchemaMap = None) -> None:
        """Construct a new schema manager."""

        if initial is None:
            initial = {}
        self.schemas: SchemaMap = initial

    def __getitem__(self, arg: str) -> Validator:
        """Directly access the schemas by key."""

        return self.schemas[arg]

    def get(self, cls: Type) -> Validator:
        """Get a validator from the name of a class reference."""

        return self[cls.__name__]

    def add(self, path: Path, name: str = None, **kwargs) -> Validator:
        """
        Add a schema from a given path. If 'name' is not provided, the basename
        of the file (minus suffix) is used.
        """

        if name is None:
            name = get_file_name(str(path))
        result = load_schema(path, **kwargs)
        assert name not in self.schemas
        self.schemas[name] = result
        return result

    def load_dir(self, path: Path, **kwargs) -> SchemaMap:
        """Add schemas loaded from a directory."""

        self.schemas.update(load_schema_dir(path, **kwargs))
        return self.schemas
