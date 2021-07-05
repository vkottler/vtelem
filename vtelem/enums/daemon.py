"""
vtelem - Enumeration definitions for daemons.
"""

# built-in
from enum import IntEnum
from typing import Optional


class DaemonState(IntEnum):
    """An enumeration of all valid daemon states."""

    ERROR = 0
    IDLE = 1
    STARTING = 2
    RUNNING = 3
    PAUSED = 4
    STOPPING = 5


class DaemonOperation(IntEnum):
    """A declaration of the actions that can be performed on a daemon."""

    NONE = 0
    START = 1
    STOP = 2
    PAUSE = 3
    UNPAUSE = 4
    RESTART = 5


def operation_str(operation: DaemonOperation) -> str:
    """Convert an operation enum to a String."""
    return operation.name.lower()


def is_operation(operation: str) -> bool:
    """Check if a provided String is a valid daemon operation."""

    for oper in DaemonOperation:
        if operation == operation_str(oper):
            return True
    return False


def str_to_operation(operation: str) -> Optional[DaemonOperation]:
    """Find an operation enum based on the provided stream."""

    for known_op in DaemonOperation:
        if operation_str(known_op) == operation.lower():
            return known_op
    return None
