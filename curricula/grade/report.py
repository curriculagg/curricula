from typing import List, Dict
from dataclasses import dataclass, field

from .resource import Resource
from .task import Result


@dataclass
class Report(Resource):
    """The final report returned by the testing framework."""

    lookup: Dict[str, Result] = field(default_factory=list)
    results: List[Result] = field(default_factory=list)

    def check(self, task_name: str) -> bool:
        result = self.lookup[task_name]
        return result.complete and result.passed

    def add(self, result: Result):
        self.lookup[result.task.name] = result
        return self.results.append(result)

    def dump(self):
        return [result.dump() for result in self.results]
