import importlib.util
import json
import sys
import timeit
from typing import Dict, Optional, Iterable, Iterator, Tuple
from pathlib import Path
from dataclasses import dataclass

from .grader import Grader
from .report import AssignmentReport, ProblemReport
from .resource import Context
from .exception import GraderException
from ..shared import *
from ..library.utility import timed
from ..log import log

PASSED = "\u2713"
FAILED = "\u2717"


def import_grader(tests_path: Path, grader_name: str = "grader") -> Grader:
    """Import a grader from a tests file."""

    sys.path.insert(0, str(tests_path.parent))
    spec = importlib.util.spec_from_file_location(f"{tests_path.parent}.tests", str(tests_path))
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    grader = getattr(tests, grader_name)
    sys.path.pop(0)

    return grader


def print_reports(target_path: Path, reports: Dict[str, ProblemReport], options: dict):
    """Print reports to terminal."""

    print(f"{target_path}")
    for problem_short, report in reports.items():
        print(f"  {problem_short}: {report.statistics()}")
        if not options.get("concise"):
            for result in report.results:
                print(f"    {PASSED if result.complete and result.passed else FAILED} {result.task.name}")


@dataclass(eq=False)
class Manager:
    """A container for multiple graders in an assignment."""

    graders: Dict[str, Grader]
    schema: dict

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
            except GraderException:
                log.error(f"grader for {problem_short} failed to check")
                return None

            graders[problem_short] = grader

        return Manager(graders=graders, schema=schema)

    @timed(name="run", printer=log.info)
    def run_single(self, target_path: Path, **options) -> AssignmentReport:
        """Run all tests on a submission and return a dict of results."""

        log.info(f"running {target_path}")
        reports = AssignmentReport()

        for problem_short, grader in self.graders.items():
            log.debug(f"running problem {problem_short}")
            problem_schema = self.schema["problems"][problem_short]
            context = Context(
                target_path=target_path,
                problem_short=problem_short,
                problem_directory=target_path.joinpath(problem_schema["directory"]),
                options=options)

            try:
                reports[problem_short] = grader.run(context=context)
            except GraderException:
                return reports

        if options.get("report"):
            print_reports(target_path, reports, options)

        return reports

    def run_batch(self, target_paths: Iterable[Path], **options) -> Iterator[Tuple[Path, AssignmentReport]]:
        """Run multiple reports, map directory to report."""

        # Start timer
        start = timeit.default_timer()

        for target_path in target_paths:
            yield target_path, self.run_single(target_path, **options)

        elapsed = timeit.default_timer() - start
        log.info(f"finished batch in {round(elapsed, 5)} seconds")
