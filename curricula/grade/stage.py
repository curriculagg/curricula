from typing import List, Type, Callable

from .task import Task, Runnable, Dependencies, Result
from .exception import GraderException

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

            name = details.pop("name", runnable.__qualname__)
            description = details.pop("description", runnable.__doc__)
            dependencies = Dependencies.from_details(details)

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
                Result=result_type))
            return runnable

        return decorator
