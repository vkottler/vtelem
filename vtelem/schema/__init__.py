"""
vtelem - A module for managing schema data.
"""

# built-in
from pathlib import Path
from typing import Dict

# third-party
from cerberus import Validator
from datazen.parsing import load
from datazen.load import load_dir

SchemaMap = Dict[str, Validator]


def load_schema(path: Path, **kwargs) -> Validator:
    """Load data from a file and create a schema validator from it."""

    assert path.is_file()
    data, loaded = load(str(path), {}, {}, is_template=False)
    assert loaded
    return Validator(data, **kwargs)


def load_schema_dir(path: Path, **kwargs) -> SchemaMap:
    """
    Load schemas from a directory, using file names (minus suffixes) as keys.
    """

    assert path.is_dir()
    data = load_dir(str(path), {}, are_templates=False)

    schemas: SchemaMap = {}
    for key, value in data.items():
        schemas[key] = Validator(value, **kwargs)
    return schemas
