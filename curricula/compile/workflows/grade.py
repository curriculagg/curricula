import json

from ..models import CompilationAssignment
from ..framework import Workflow, TargetResult
from ...shared import Paths


class GradeWorkflow(Workflow):
    """Grades the solution and writes the report to the artifact root."""

    def run(self, assignment: CompilationAssignment, result: TargetResult):
        """Main."""

        if not self.configuration.options.get("grade"):
            return

        if not result["grading"].compiled and not result["solution"].compiled:
            return

        from ...grade import run
        from ...grade.models import GradingAssignment
        from ...grade.tools.format import format_report_markdown
        from ...grade.tools.diagnostics import get_diagnostics

        grading_path = self.configuration.artifacts_path.joinpath(Paths.GRADING)
        solution_path = self.configuration.artifacts_path.joinpath(Paths.SOLUTION)
        report_path = self.configuration.artifacts_path.joinpath("solution.report.json")
        formatted_report_path = self.configuration.artifacts_path.joinpath("solution.report.md")

        assignment = GradingAssignment.read(grading_path)
        report = run(assignment, solution_path, options=self.configuration.options)

        with report_path.open("w") as file:
            json.dump(report.dump(), file, indent=2)

        with formatted_report_path.open("w") as file:
            file.write(format_report_markdown(
                assignment=assignment,
                report_path=report_path,
                options=self.configuration.options))

        get_diagnostics(assignment, report_path)
