from dataclasses import dataclass


@dataclass
class TaskSummary:
    """Statistics about task results."""

    task: dict
    total: int = 0
    complete: int = 0
    passed: int = 0


@dataclass
class OverallSummary:
    """Statistics about a set of tests."""

    total: int = 0
    setup: int = 0
