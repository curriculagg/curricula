import jinja2
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

root = Path(__file__).absolute().parent
log = logging.getLogger("curricula")


def pretty(decimal: Decimal) -> str:
    """Display a number nicely."""

    if int(decimal) == decimal:
        return str(int(decimal))
    return str(round(decimal, 3)).rstrip("0")


def percentage(d: Any, digits: int = 1) -> str:
    """Convert a float to a nice-looking percentage."""

    converted = d if isinstance(d, Decimal) else Decimal(str(d))
    converted *= 100
    if converted == converted.to_integral_value():
        return f"{int(converted)}%"
    return f"{round(converted, digits)}%"


JINJA2_FILTERS = {
    "pretty": pretty,
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y"),
    "percentage": percentage,
}


def jinja2_create_environment(
        default_template_path: Path,
        custom_template_path: Path = None,
        assignment_path: Path = None,
        problem_paths: Dict[str, Path] = None) -> jinja2.Environment:
    """Configure a jinja2 environment."""

    log.debug("creating jinja2 environment")

    # Create a loader in the order of arguments
    mapping = {}
    if assignment_path:
        mapping["assignment"] = jinja2.FileSystemLoader(str(assignment_path))
    if problem_paths:
        for key, path in problem_paths.items():
            mapping[key] = jinja2.FileSystemLoader(str(path))

    # Add custom templates
    mapping["template"] = jinja2.ChoiceLoader(
        ([jinja2.FileSystemLoader(str(custom_template_path))] if custom_template_path is not None else []) +
        [jinja2.FileSystemLoader(str(default_template_path))])
    loader = jinja2.PrefixLoader(mapping, delimiter=":")

    # Actually create the environment, we use square brackets to avoid
    # clashing with Jekyll
    environment = jinja2.Environment(
        loader=loader,
        block_start_string="[%",
        block_end_string="%]",
        variable_start_string="[[",
        variable_end_string="]]",
        comment_start_string="[#",
        comment_end_string="#]",
        autoescape=False,
        keep_trailing_newline=False,
        trim_blocks=True,
        lstrip_blocks=True)

    # Custom filters
    environment.filters.update(JINJA2_FILTERS)

    return environment
