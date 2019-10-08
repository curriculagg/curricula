from typing import List
from dataclasses import dataclass, field

from .resource import Resource
from .task import Result


@dataclass
class Report(Resource):
    """The final report returned by the testing framework."""

    results: List[Result] = field(default_factory=list)

    def add(self, result: Result):
        return self.results.append(result)

    def dump(self):
        return [result.dump() for result in self.results]
