import jinja2
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

root = Path(__file__).absolute().parent
log = logging.getLogger("curricula")


def percentage(d: Any, digits: int = 1) -> str:
    """Convert a float to a nice-looking percentage."""

    converted = d if isinstance(d, Decimal) else Decimal(str(d))
    converted *= 100
    if converted == converted.to_integral_value():
        return f"{int(converted)}%"
    return f"{round(converted, digits)}%"


JINJA2_FILTERS = {
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y"),
    "percentage": percentage,
}


def jinja2_create_environment(**template_paths: Path) -> jinja2.Environment:
    """Configure a jinja2 environment."""

    log.debug("creating jinja2 environment")

    # Create a loader in the order of arguments
    loader = jinja2.PrefixLoader({
        key: jinja2.FileSystemLoader(str(path)) for key, path in template_paths.items()
    }, delimiter=":")

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
        keep_trailing_newline=True)

    # Custom filters
    environment.filters.update(JINJA2_FILTERS)

    return environment
