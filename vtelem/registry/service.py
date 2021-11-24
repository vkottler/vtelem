"""
vtelem - Contains a class for managing known services.
"""

# built-in
from typing import List, Tuple

# internal
from vtelem.registry import Registry

Service = List[Tuple[str, int]]


class ServiceRegistry(Registry[Service]):
    """A class for managing services by name, hostname and port."""

    def __init__(
        self, initial_services: List[Tuple[str, Service]] = None
    ) -> None:
        """Construct a new service registry."""

        super().__init__("services", initial_services)
