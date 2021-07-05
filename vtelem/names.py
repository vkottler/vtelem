"""
vtelem - Common name manipulations.
"""

# built-in
import re
from typing import Type


def class_to_snake(class_obj: Type) -> str:
    """Convert a CamelCase named class to a snake_case String."""

    return to_snake(class_obj.__name__)


def to_snake(name: str) -> str:
    """Convert a CamelCase String to snake_case."""

    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
