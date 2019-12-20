import timeit
from typing import Callable
from functools import wraps


def name_from_doc(test: Callable):
    """Get a function's name from it's docstring.

    Either up until the first period or the end of the line, if more
    control is necessary use the register argument.
    """

    d = test.__doc__
    if d is not None:
        return d[:min(d.find("."), d.find("\n"))]
    return None


def timed(name: str = "", printer: Callable[[str], None] = print):
    """Add a timer around a function."""

    def wrapper(func):

        @wraps(func)
        def wrapped(*args, **kwargs):
            start = timeit.default_timer()
            result = func(*args, **kwargs)
            elapsed = timeit.default_timer() - start
            printer(f"{name} finished in {round(elapsed, 5)} seconds")
            return result

        return wrapped
    return wrapper
