"""
vtelem - A module implementing a simple cache for arbitrary data.
"""

# built-in
import os
import shutil
from typing import List

# third-party
from vcorelib.dict import merge
from vcorelib.io import ARBITER


class DataCache:
    """A class that allows dictionary data to be easily backed to disk."""

    def __init__(self, cache_dir: str) -> None:
        """Construct a new data cache."""

        self.data: dict = {}
        self.loaded: List[str] = []
        self.cache_dir = cache_dir
        self.load(self.cache_dir)

    def load(self, directory: str) -> None:
        """Load a new directory into the cache."""

        if directory in self.loaded:
            return

        os.makedirs(self.cache_dir, exist_ok=True)
        self.data = merge(
            self.data,
            ARBITER.decode_directory(
                directory, require_success=True, recurse=True
            ).data,
        )
        self.loaded.append(directory)

    def write(self) -> None:
        """Write cache contents to disk."""

        ARBITER.encode_directory(self.cache_dir, self.data, "yaml")

    def clean(self) -> None:
        """Clean the cache contents from disk."""

        self.data = {}
        self.loaded = []
        shutil.rmtree(self.cache_dir)
        self.load(self.cache_dir)
