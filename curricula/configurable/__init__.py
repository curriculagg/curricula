import jinja2
import json
from pathlib import Path


JINJA2_FILTERS = {
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y"),
}


def create_jinja2_environment(**options) -> jinja2.Environment:
    """Configure a jinja2 environment."""

    root = Path(__file__).absolute().parent
    with root.joinpath("jinja2.json").open() as file:
        jinja2_config = json.load(file)

    environment = jinja2.Environment(**jinja2_config, **options)
    environment.filters.update(JINJA2_FILTERS)
    return environment
