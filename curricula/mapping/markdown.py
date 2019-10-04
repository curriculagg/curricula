import jinja2


JINJA2_FILTERS = {
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y"),
}


def jinja2_create_environment(**options) -> jinja2.Environment:
    """Configure a jinja2 environment."""

    environment = jinja2.Environment(
        block_start_string="[%",
        block_end_string="%]",
        variable_start_string="[[",
        variable_end_string="]]",
        comment_start_string="[#",
        comment_end_string="#]",
        autoescape=False,
        **options)
    environment.filters.update(JINJA2_FILTERS)
    return environment
