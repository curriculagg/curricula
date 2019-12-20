import jinja2
from decimal import Decimal
from pathlib import Path
from typing import List

root = Path(__file__).absolute().parent


def percentage(d: float, digits: int = 1) -> str:
    """Convert a float to a nice-looking percentage."""

    converted = Decimal(str(d)) * 100
    if converted == converted.to_integral_value():
        return f"{int(converted)}%"
    return f"{round(converted, digits)}%"


JINJA2_FILTERS = {
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y"),
    "percentage": percentage,
}


def jinja2_create_environment(template_path: Path, *template_paths: List[Path], **options) -> jinja2.Environment:
    """Configure a jinja2 environment."""

    print(str(template_path))
    loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(str(template_path)),
        *map(lambda p: jinja2.FileSystemLoader(str(p)), template_paths)])

    environment = jinja2.Environment(
        loader=loader,
        block_start_string="[%",
        block_end_string="%]",
        variable_start_string="[[",
        variable_end_string="]]",
        comment_start_string="[#",
        comment_end_string="#]",
        autoescape=False,
        keep_trailing_newline=True,
        **options)

    # Custom filters
    environment.filters.update(JINJA2_FILTERS)

    return environment
