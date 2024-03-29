"""
vtelem - A module for creating functions based on a daemon manager.
"""

# built-in
import json
from typing import List, Tuple

# internal
from vtelem.daemon.command_queue import CommandQueueDaemon
from vtelem.daemon.manager import DaemonManager
from vtelem.enums.daemon import DaemonOperation, is_operation, operation_str
from vtelem.types.command_queue_daemon import ResultCbType


def create_daemon_manager_commander(
    manager: DaemonManager,
    daemon: CommandQueueDaemon,
    result_cb: ResultCbType = None,
    command_name: str = "daemon",
) -> None:
    """Register a handler to a command queue for a daemon manager."""

    def daemon_commander(cmd: dict) -> Tuple[bool, str]:
        """Attempt to run a daemon-manager command."""

        if "operation" not in cmd:
            return False, "no command 'operation' provided"

        oper = cmd["operation"].lower()
        if is_operation(oper):
            if "daemons" not in cmd or not isinstance(cmd["daemons"], list):
                return False, f"'daemons' not provided as a list for '{oper}'"

            # allow 'all' to be a special key
            daemons = cmd["daemons"]
            if "all" in daemons:
                daemons = list(manager.states().keys())

            # execute all of the requested commands
            results = {}
            bool_results: List[bool] = []
            for daemon_name in daemons:
                result = manager.perform_str(daemon_name, oper)
                bool_results.append(result)
                results[daemon_name] = result
            state_data = manager.states()
            state_data["results"] = results
            return all(bool_results), json.dumps(state_data)

        if oper == "states":
            return True, json.dumps(manager.states())

        return False, f"unknown 'operation' '{oper}'"

    oper_strs = [operation_str(op) for op in DaemonOperation]
    ops_str = ", ".join(f"'{val}'" for val in oper_strs)
    daemon.register_consumer(
        command_name, daemon_commander, result_cb, f"{ops_str} daemons"
    )
