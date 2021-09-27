"""
vtelem - Utilities for accessing file resouces for tests.
"""

# built-in
import os
from pathlib import Path
import pkg_resources


def get_resource(resource_name: str, pkg: str = __name__) -> str:
    """Locate the path to a test resource."""

    resource_path = os.path.join("data", resource_name)
    return pkg_resources.resource_filename(pkg, resource_path)


def get_test_schema(filename: str, pkg: str = __name__) -> Path:
    """Get a schema file from test data."""

    return Path(get_resource(os.path.join("schemas", filename), pkg))
