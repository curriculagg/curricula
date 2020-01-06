from dataclasses import dataclass, field
from typing import Dict, Any

from . import GraderConfiguration
from ..exception import GraderException
from ..task import Task, Result
from ...log import log

Nothing = object()


@dataclass(eq=False)
class OutputConfiguration(GraderConfiguration):
    """Options for task and result schema."""

    task_details: Dict[str, Any] = field(default_factory=dict)
    result_details: Dict[str, Any] = field(default_factory=dict)

    def add_required_task_detail(self, name: str, default: Any = Nothing):
        """Add a required task detail."""

        self.task_details[name] = default

    def add_required_result_detail(self, name: str, default: Any = Nothing):
        """Add a required task detail."""

        self.result_details[name] = default

    def check_task(self, task: Task):
        """Confirm details are fulfilled."""

        for detail_name, detail_default in self.task_details.items():
            if detail_name not in task.details:
                if detail_default is Nothing:
                    log.error(f"missing required detail {detail_name} in task {task.name}")
                    raise GraderException()
                task.details[detail_name] = detail_default

    def check_result(self, result: Result):
        """Confirm details are fulfilled."""

        for detail_name, detail_default in self.task_details.items():
            if detail_name not in result.details:
                if detail_default is Nothing:
                    log.error(f"missing required detail {detail_name} from result of task {result.task.name}")
                    raise GraderException()
                result.details[detail_name] = detail_default
