from typing import Callable


def name_from_doc(test: Callable):
    """Get a test's name from it's docstring.

    Either up until the first period or the end of the line, if more
    control is necessary use the register argument.
    """

    d = test.__doc__
    if d is not None:
        return d[:min(d.find("."), d.find("\n"))]
    return None
