from typing import List, Type, Callable
from decimal import Decimal

from .task import Task, Runnable, Dependencies, Result
from .exception import GraderException
from ..library.debug import get_source_location

__all__ = ("GraderStage", "Registrar")

Registrar = Callable[[Runnable], Runnable]
RegistrarFactory = Callable[[dict, Type[Result]], Registrar]


class GraderStage:
    """Management for setup, test, and teardown stages."""

    name: str
    tasks: List[Task]

    def __init__(self):
        """Initialize new grader stage with empty tasks."""

        self.tasks = []

    def registrar(self, details: dict, result_type: Type[Result]):
        """Generate a registrar for tasks.

        This is to be used internally within named registration
        endpoints and returns a decorator.
        """

        def decorator(runnable: Runnable) -> Runnable:
            """Put the function in a correctness object."""

            name = details.pop("name", None) or runnable.__qualname__
            description = details.pop("description", None) or runnable.__doc__
            weight = Decimal(details.pop("weight", 1))
            dependencies = Dependencies.from_details(details)
            tags = details.pop("tags", set())

            for existing_task in self.tasks:
                if existing_task.name == name:
                    raise GraderException(f"Duplicate task name \"{name}\"")

            # Create task, append
            self.tasks.append(Task(
                name=name,
                description=description,
                stage=self.name,
                kind=result_type.kind,
                dependencies=dependencies,
                runnable=runnable,
                details=details,
                weight=weight,
                source=get_source_location(2),
                tags=tags,
                Result=result_type))
            return runnable

        return decorator
