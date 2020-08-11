from pathlib import Path

from ..models import CompilationAssignment
from ..framework import Workflow, TargetResult
from ...shared import Paths, Files
from ...log import log
from ...library.files import copy_directory, move


class SiteWorkflow(Workflow):
    """Grades the solution and writes the report to the artifact root."""

    def run(self, assignment: CompilationAssignment, result: TargetResult):
        """Main."""

        if not self.configuration.options.get("site"):
            return

        if not result["instructions"].compiled:
            return

        site_path = Path(self.configuration.options["site"])
        if not site_path.parent.exists():
            log.error("site parent path does not exist, cancelling pipeline")
            return

        log.info(f"pipelining instructions to site {site_path}")
        copy_directory(
            source=self.configuration.artifacts_path.joinpath(Paths.INSTRUCTIONS),
            destination=site_path,
            merge=False)
        move(site_path.joinpath(Files.README), site_path.joinpath("index.md"))
