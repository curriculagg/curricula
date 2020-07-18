import json
from pathlib import Path

from curricula.library.printer import Printer
from ..models import GradingAssignment
from ..report import AssignmentReport


def get_diagnostics(grading_path: Path, assignment_report_path: Path) -> str:
    """Check if tests passed, displaying errors."""

    assignment = GradingAssignment.read(grading_path)
    with assignment_report_path.open() as file:
        assignment_report = AssignmentReport.load(json.load(file), assignment)

    output = Printer()

    for problem in assignment.problems:
        problem_report = assignment_report[problem.short]

        results_passing_count = sum(1 for _ in filter(lambda p: p.passing, problem_report.results.values()))

        output.print(f"Problem {problem.short}: {results_passing_count}/{len(problem_report.results.values())}")
        output.indent()

        for task in problem.grader.tasks:
            result = problem_report.get(task.name)
            if result is None:
                continue

            if not result.complete:
                output.print(f"✗ {task.name} did not complete")
            elif not result.passing:
                output.print(f"✗ {task.name} failed")
                output.indent()
                if result.error:
                    if result.error.location:
                        output.print(f"Reason: {result.error.description}")
                        output.print(f"Location: {result.error.location}")
                    if result.error.traceback:
                        output.print("Traceback: ")
                        output.print(result.error.traceback.strip(), indentation=2)
                    if result.error.expected:
                        output.print("Expected:")
                        output.print(result.error.expected, indentation=2)
                    if result.error.received:
                        output.print("Received:")
                        output.print(result.error.received, indentation=2)
                output.dedent()
            else:
                output.print(f"✓ {task.name} passed")

        output.dedent()
    return str(output)
