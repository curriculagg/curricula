from pathlib import Path

from ..library.utility import timed
from ..log import log

from .compilation import CurriculaTarget, Configuration


@timed("compile", printer=log.info)
def compile(assignment_path: Path, artifacts_path: Path, custom_template_path: Path = None, options: dict = None):
    """Build the assignment at a given path."""

    configuration = Configuration(
        assignment_path=assignment_path,
        artifacts_path=artifacts_path,
        custom_template_path=custom_template_path,
        options=options)
    target = CurriculaTarget(configuration)
    target.compile()
