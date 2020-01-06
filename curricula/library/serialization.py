import json
from typing import Any, TextIO


def truncate(string: str, length: int, append: str = "...") -> str:
    """Shorthand for cutting off long strings.

    If length is zero or negative, the string will not be checked or
    truncated. The original string will be returned.
    """

    if len(string) > length > 0:
        return string[:length - len(append)] + append
    return string


def descend_and_truncate(o: Any, length: int, append: str = "..."):
    """Truncate strings in a JSON object."""

    if isinstance(o, str):
        return truncate(o, length, append)
    if isinstance(o, dict):
        for key, value in o.items():
            o[key] = descend_and_truncate(value, length, append)
    if isinstance(o, list):
        for i, item in enumerate(o):
            o[i] = descend_and_truncate(item, length, append)
    return o


def dump(o: Any, file: TextIO, no_truncate: bool = False, **options):
    """Write an object to a file."""

    if not no_truncate:
        descend_and_truncate(o, 100_000)
    json.dump(o, file, **options)


def load(file: TextIO):
    """Read data from a file."""

    return json.load(file)
