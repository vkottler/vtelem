"""
vtelem - Test message cache correctness.
"""

# built-in
import tempfile

# module under test
from vtelem.message.cache import MessageCache
from vtelem.types.frame import MessageType

# internal
from tests.message import LONG_MESSAGE, create_env, parse_frames


def test_message_cache_basic():
    """Test basic correctness of the message cache."""

    framer, env = create_env()
    frames, _ = framer.serialize_message_str(LONG_MESSAGE)
    parsed = parse_frames(env, frames)

    with tempfile.TemporaryDirectory() as cache_dir:
        cache = MessageCache(cache_dir)
        for message in parsed:
            cache.ingest(message)

        # ingest the messages again
        for message in parsed:
            cache.ingest(message)

        completed = cache.complete(MessageType.TEXT)
        assert len(completed) == 1

        # confirm we are able to ingest this message
        assert cache.content(MessageType.TEXT, completed[0] + 1) is None
        assert cache.content_str(MessageType.TEXT, completed[0] + 1) is None
        _, data = cache.content_str(MessageType.TEXT, completed[0])
        assert data == LONG_MESSAGE

        # confirm the cache can be loaded
        cache.write()
        new_cache = MessageCache(cache_dir)
        print(new_cache.data)
        assert len(new_cache.complete(MessageType.TEXT)) == 1
        _, data = new_cache.content_str(MessageType.TEXT, completed[0])
        assert data == LONG_MESSAGE
