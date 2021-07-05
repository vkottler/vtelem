"""
vtelem - Test the state machine module's correctness.
"""

# module under test
from vtelem.classes.state import State
from vtelem.classes.state_machine import StateMachine
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.mtu import DEFAULT_MTU


def test_state_machine_basic():
    """Test basic state machine operation."""

    env = TelemetryEnvironment(DEFAULT_MTU)
    iterations = 0

    def sample_enter(_: str, __: dict) -> bool:
        """Does nothing."""
        return (iterations % 4) == 0

    total_states = 10
    next_state = 1

    def sample_run(_: dict) -> str:
        """Transitions to the next numerical state name."""
        nonlocal next_state
        result = str(next_state)
        next_state += 1
        if next_state >= total_states:
            next_state = 0
        return result

    def sample_leaving(_: str, __: dict) -> bool:
        """Does nothing."""
        return (iterations % 2) == 0

    states = []
    for i in range(total_states):
        states.append(
            State(str(i), sample_run, sample_enter, sample_leaving, env=env)
        )
    assert states[0] != states[1]

    sm_test = StateMachine("test", states, env=env)
    with sm_test.data() as data:
        data["a"] = "a"
        data["b"] = "b"
        data["c"] = "c"
    sm_test.run({"d": "d", "e": "e", "f": "f"})
    for _ in range(100):
        sm_test.run()
        iterations += 1
