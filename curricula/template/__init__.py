import jinja2
from decimal import Decimal
from pathlib import Path

root = Path(__file__).absolute().parent


def percentage(d: float) -> str:
    converted = Decimal(str(d)) * 100
    if converted == converted.to_integral_value():
        return f"{int(converted)}%"
    return f"{round(converted, 1)}%"


JINJA2_FILTERS = {
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y"),
    "percentage": percentage,
}


def jinja2_create_environment(custom_template_path: Path = None, **options) -> jinja2.Environment:
    """Configure a jinja2 environment."""

    if custom_template_path is None:
        loader = jinja2.FileSystemLoader(str(root))
    else:
        loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(str(root)),
            jinja2.FileSystemLoader(str(custom_template_path))])

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
    environment.filters.update(JINJA2_FILTERS)
    return environment
