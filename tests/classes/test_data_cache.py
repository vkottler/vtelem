"""
vtelem - Tests for the DataCache class.
"""

# built-in
import tempfile

# module under test
from vtelem.classes.data_cache import DataCache


def test_data_cache_simple():
    """Test basic correctness of the data cache."""

    sample_data = {"a": 1, "b": 2, "c": 3}

    with tempfile.TemporaryDirectory() as cache_dir:
        cache = DataCache(cache_dir)
        cache.load(cache_dir)
        cache.clean()

        cache.data["test"] = sample_data
        cache.write()

        new_cache = DataCache(cache_dir)
        assert cache.data == new_cache.data
