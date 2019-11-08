"""Convenience functions for output manipulation."""

from ...library.process import Runtime
from ...test.correctness import CorrectnessResult

from typing import List, Iterable, AnyStr, Union, Sized

__all__ = ("as_lines", "lines_match", "compare_stdout")


def as_lines(string: AnyStr) -> List[AnyStr]:
    """Strip and split by newline."""

    return string.strip().split("\n" if isinstance(string, str) else b"\n")


AnyStrSequence = Union[Iterable[AnyStr], Sized]


def lines_match(a: AnyStrSequence, b: AnyStrSequence) -> bool:
    """Check ordered equality.

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


def compare_stdout(runtime: Runtime, test_out_line_lists: List[List[bytes]]) -> CorrectnessResult:
    """Check stdout for matching output."""

    if runtime.error is not None:
        return CorrectnessResult(complete=False, passed=False, runtime=runtime)

    out_lines = runtime.stdout.strip().split(b"\n")
    passed = any(lines_match(out_lines, test_out_lines) for test_out_lines in test_out_line_lists)

    expected_out_lines = []
    for out_lines in test_out_line_lists:
        expected_out_lines.append(b"\n".join(out_lines).decode(errors="replace"))
    details = dict() if passed else dict(expected=expected_out_lines)

    return CorrectnessResult(passed=passed, runtime=runtime, **details)
