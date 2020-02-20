from typing import List, Type, Callable

from .task import Task, Runnable, Result
from ..log import log

__all__ = ("GraderStage", "Registrar")

Registrar = Callable[[Runnable], Runnable]
RegistrarFactory = Callable[[dict, Type[Result]], Registrar]


def create_registrar_factory(stage: str, task_list: List[Task]) -> RegistrarFactory:
    """A third-level decorator to reuse code."""

    def create_registrar(details: dict, result_type: Type[Result]) -> Registrar:
        """Differentiate based on the kind of result."""

        def decorator(runnable: Runnable) -> Runnable:
            """Put the function in a correctness object."""

            name = details.pop("name", runnable.__qualname__)
            description = details.pop("description", runnable.__doc__)

            # Get dependencies
            if "dependencies" in details:
                if "dependency" in details:
                    log.error("only one of dependency and dependencies may be specified")
                    raise ValueError()
                dependencies = details.pop("dependencies")
            elif "dependency" in details:
                dependencies = (details.pop("dependency"),)
            else:
                dependencies = ()

            for existing_task in task_list:
                if existing_task.name == name:
                    raise ValueError(f"Duplicate task name \"{name}\"")

            # Create task, append
            task_list.append(Task(
                name=name,
                description=description,
                stage=stage,
                kind=result_type.kind,
                dependencies=dependencies,
                runnable=runnable,
                details=details,
                result_type=result_type))
            return runnable

        return decorator

    return create_registrar


class GraderStage:
    """Management for setup, test, and teardown stages."""

    name: str
    tasks: List[Task]
    create_registrar: RegistrarFactory

    def __init__(self):
        self.tasks = []
        self.create_registrar = create_registrar_factory(stage=self.name, task_list=self.tasks)
