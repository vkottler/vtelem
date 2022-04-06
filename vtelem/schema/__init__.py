"""
vtelem - A module for managing schema data.
"""

# built-in
from pathlib import Path
from typing import Dict

# third-party
from cerberus import Validator
from datazen.code import ARBITER
from datazen.load import load_dir

SchemaMap = Dict[str, Validator]


def load_schema(path: Path, **kwargs) -> Validator:
    """Load data from a file and create a schema validator from it."""

    return Validator(ARBITER.decode(path, require_success=True).data, **kwargs)


def load_schema_dir(path: Path, **kwargs) -> SchemaMap:
    """
    Load schemas from a directory, using file names (minus suffixes) as keys.
    """

    assert path.is_dir()
    data = load_dir(str(path), {}, are_templates=False)[0]

    schemas: SchemaMap = {}
    for key, value in data.items():
        schemas[key] = Validator(value, **kwargs)
    return schemas
