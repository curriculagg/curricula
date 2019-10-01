"""Convenience functions for output manipulation."""

from typing import List, Tuple, Iterable

__all__ = ("as_lines", "lines_match")


def as_lines(string: str) -> List[str]:
    """Strip and split by newline."""

    return string.strip().split("\n")


def lines_match(test: List[str], correct: Tuple[str]) -> Iterable:
    """Check equality without order.

    Returns a boolean indicating correctness and a list of errors
    encountered while checking.
    """

    if len(test) != len(correct):
        difference = len(test) - len(correct)
        yield False
        yield "{} {} outputs".format(abs(difference), "extra" if difference > 0 else "missing")
        return

    unexpected = []
    unmatched = list(correct)
    for line in test:
        if line in unmatched:
            unmatched.remove(line)
        else:
            unexpected.append(line)

    count = len(unexpected)
    if count > 0:
        yield False
        yield "{} unexpected outputs".format(count)
        for i in range(min(count, 5)):
            yield "  " + unexpected[i]
        if count > 5:
            yield "  ..."
        return

    yield True
