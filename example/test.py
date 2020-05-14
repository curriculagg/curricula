import sys
import logging
from pathlib import Path

root = Path(__file__).absolute().parent
sys.path.insert(0, str(root.parent))

from curricula.compile import build
from curricula.grade.manager import Manager
from curricula.grade.tools.format import format_report_markdown
from curricula.shared import Paths
from curricula.library.serialization import dump
from curricula.log import log


def main():
    """Build the example assignment and grade the solution."""

    log.setLevel(logging.DEBUG)

    # Build
    template_path = root.joinpath("template")
    artifacts_path = root.joinpath("artifacts", "assignment")
    build(
        template_path=template_path,
        assignment_path=root.joinpath("assignment"),
        artifacts_path=artifacts_path)

    # Grade
    manager = Manager.load(artifacts_path.joinpath(Paths.GRADING))
    report = manager.run_single(target_path=artifacts_path.joinpath(Paths.SOLUTION))

    # Output
    report_path = root.joinpath("reports", "report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as file:
        dump(report.dump(), file, indent=2)
    with report_path.parent.joinpath("report.md").open("w") as file:
        file.write(format_report_markdown(
            grading_path=artifacts_path.joinpath(Paths.GRADING),
            template_path=template_path.joinpath("grade", "report.md"),
            report_path=report_path))


if __name__ == '__main__':
    main()
