"""
vtelem - Utilities for accessing file resouces for tests.
"""

# built-in
import os
import pkg_resources


def get_resource(resource_name: str) -> str:
    """Locate the path to a test resource."""

    resource_path = os.path.join("data", resource_name)
    return pkg_resources.resource_filename(__name__, resource_path)
