"""Convenience functions for output manipulation."""

from typing import List, Iterable, AnyStr, Union, Container

__all__ = ("as_lines", "lines_match")


def as_lines(string: AnyStr) -> List[AnyStr]:
    """Strip and split by newline."""

    return string.strip().split("\n" if isinstance(string, str) else b"\n")


MaybeContainer = Union[Iterable, Container]


def lines_match(a: MaybeContainer[AnyStr], b: MaybeContainer[AnyStr]) -> bool:
    """Check equality without order.

    Returns a boolean indicating correctness and a list of errors
    encountered while checking.
    """

    if hasattr(a, "__len__") and hasattr(a, "__len__"):
        if len(a) != len(b):
            return False

    for x, y in zip(a, b):
        if x != y:
            return False

    return True
