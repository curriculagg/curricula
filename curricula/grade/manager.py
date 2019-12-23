import importlib.util
import json
import sys
from typing import Dict, Optional, Iterable, Iterator, Tuple
from pathlib import Path
from dataclasses import dataclass

from .grader import Grader
from .report import Report
from .resource import Context
from ..core.shared import *
from ..core.models import Assignment
from ..library.log import log


def import_grader(tests_path: Path, grader_name: str = "grader") -> Grader:
    """Import a grader from a tests file."""

    sys.path.insert(0, str(tests_path.parent))
    spec = importlib.util.spec_from_file_location(f"{tests_path.parent}.tests", str(tests_path))
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    grader = getattr(tests, grader_name)
    sys.path.pop(0)

    return grader


def generate_grading_schema(grading_path: Path, assignment: Assignment) -> dict:
    """Generate a JSON schema describing the grading package.

    This method requires the grading artifact to already have been
    aggregated, as it has to access the individual problem graders to
    dump their task summaries.
    """

    result = dict(title=assignment.title, problems=dict())
    for problem in assignment.problems:
        if "automated" in problem.grading.process:
            grader = import_grader(grading_path.joinpath(problem.short, Files.TESTS))
            result["problems"][problem.short] = dict(
                title=problem.title,
                percentage=problem.percentage,
                tasks=grader.dump())
    return result


@dataclass(eq=False)
class Manager:
    """A container for multiple graders in an assignment."""

    graders: Dict[str, Grader]

    @classmethod
    def load(cls, grading_path: Path) -> Optional["Manager"]:
        """Load a manager from a grading artifact in the file system."""

        log.debug(f"loading manager from {grading_path}")
        log.debug("reading schema")
        with grading_path.joinpath(Files.GRADING).open() as file:
            schema = json.load(file)

        log.debug("assembling graders")
        graders = {}
        for problem_short in schema["problems"]:
            log.debug(f"importing grader for {problem_short}")
            grader = import_grader(grading_path.joinpath(problem_short, Files.TESTS))

            # Check dependencies
            try:
                grader.check()
            except ValueError:
                log.error(f"grader for {problem_short} failed to check")
                return None

            graders[problem_short] = grader

        return Manager(graders)

    def run_single(self, target_path: Path, **options) -> Dict[str, Report]:
        """Run all tests on a submission and return a dict of results."""

        reports = {}
        for problem_short, grader in self.graders.items():
            context = Context(target_path, options)
            reports[problem_short] = grader.run(context=context)
        return reports

    def run_batch(self, target_paths: Iterable[Path], **options) -> Iterator[Tuple[Path, Dict[str, Report]]]:
        """Run multiple reports, map directory to report."""

        report_tree = {}
        for target_path in target_paths:
            yield target_path, self.run_single(target_path, **options)
        return report_tree
