"""
vtelem - Some Queue wrappers and 'stream' utilities.
"""

# built-in
from queue import Empty, Queue
from typing import Any, Optional

QUEUE_TIMEOUT = 2


def queue_get(queue: Queue, timeout: int = QUEUE_TIMEOUT) -> Optional[Any]:
    """
    Wrap a de-queue operation into one that will return None if the timeout
    is met.
    """

    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None


def queue_get_none(queue: Queue, timeout: int = QUEUE_TIMEOUT) -> None:
    """Attempt to get a literal 'None' from the queue."""

    result = queue.get(timeout=timeout)
    assert result is None
