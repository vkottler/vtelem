"""
vtelem - Test the file client's correctness.
"""

# module under test
from vtelem.client.file import create
from vtelem.stream import queue_get, queue_get_none

# internal
from tests import writer_environment


def test_file_client_frame_restrict():
    """Test that setting the maximum number of frames-to-decode works."""

    mtu = 64
    max_frames = 16
    writer, env = writer_environment(mtu)
    with create(writer, env, mtu, max_frames) as (client, queue):
        with writer.booted():
            frame_count = 0

            # Ensure that we write more frames than we want to decode.
            while frame_count < 2 * max_frames:
                env.advance_time(10)
                frame_count += env.dispatch_now()
            writer.await_empty()

            with client.booted(require_stop=False):
                for _ in range(max_frames):
                    assert queue_get(queue) is not None

            # Verify that no additional frames were enqueued.
            assert queue.empty()


def test_file_client_basic():
    """Test that a file client can correctly decode frames."""

    mtu = 64
    writer, env = writer_environment(mtu)
    with create(writer, env, mtu) as (client, queue):
        with writer.booted():
            for _ in range(5):
                frame_count = 0
                for _ in range(10):
                    env.advance_time(10)
                    frame_count += env.dispatch_now()
                writer.await_empty()

                # Verify that the client decodes all frames.
                with client.booted(require_stop=False):
                    for _ in range(frame_count):
                        assert queue_get(queue) is not None
                queue_get_none(queue)
