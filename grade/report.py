from typing import List
from dataclasses import dataclass, field, asdict

from .resource import Resource


@dataclass
class Entry:
    """Entry for a report."""

    kind: str
    stage: str
    name: str
    description: str
    details: dict = field(default_factory=dict)


@dataclass
class Report(Resource):
    """The final report returned by the testing framework."""

    entries: List[Entry] = field(default_factory=list)
    stage: str = "checks"

    def entry(self, kind: str, name: str, description: str, details: dict = None):
        return self.entries.append(Entry(
            kind=kind, stage=self.stage, name=name, description=description, details=details or dict()))

    def dump(self):
        return [asdict(entry) for entry in self.entries]
