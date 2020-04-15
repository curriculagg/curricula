from .task import Task
from .exception import GraderException

from typing import Dict, List, Iterable

__all__ = ("topological_sort",)


def topological_sort_visit(task: Task, lookup: Dict[str, Task], marks: Dict[Task, int], result: List[Task]):
    """Visit a node."""

    if marks[task] == 2:
        return

    if marks[task] == 1:
        raise GraderException("found cycle in task dependencies")

    marks[task] = 1
    for dependency in task.dependencies.passing | task.dependencies.complete:
        topological_sort_visit(lookup[dependency], lookup, marks, result)
    marks[task] = 2
    result.append(task)


def topological_sort(stage_tasks: Iterable[List[Task]]):
    """Order tasks by dependency."""

    lookup = {}
    marks = {}
    for tasks in stage_tasks:
        result = []
        for task in tasks:
            marks[task] = 0
            lookup[task.name] = task
        for task in tasks:
            if marks[task] != 2:
                topological_sort_visit(task, lookup, marks, result)
        tasks.clear()
        tasks.extend(result)


