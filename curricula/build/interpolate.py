import re

from .container import Assignment, Problem

VARIABLE_PATTERN = re.compile(
    r"(?<!\\)"
    r"\[\[\s*"
    r"(?P<variable>assignment|problem)\.(?P<path>[\w.]+)"
    r"(\s*\|\s*(?P<filter>\w+))?"
    r"\s*\]\]")


FILTERS = {
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y")
}


def get(obj, *keys):
    """Descend a list of string properties."""

    for key in keys:
        obj = getattr(obj, key)
    return obj


def interpolate(contents: str, assignment: Assignment, problem: Problem = None):
    """Fill in any assignment or problem variables."""

    matches = list(VARIABLE_PATTERN.finditer(contents))
    for match in reversed(matches):
        data = match.groupdict()
        variable = assignment if data["variable"] == "assignment" else problem
        result = get(variable, *data["path"].split("."))
        if data["filter"]:
            result = FILTERS[data["filter"]](result)
        contents = contents[:match.start()] + result + contents[match.end():]
    return contents
