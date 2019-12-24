"""Convenience functions for output manipulation."""

from ...library.process import Runtime
from . import CorrectnessResult

from typing import List, Iterable, AnyStr, Union, Sized, Callable
from pathlib import Path

__all__ = (
    "as_lines",
    "lines_match",
    "compare_stdout",
    "make_make_test_in_out",
    "make_exit_test")


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
    """Check stdout for matching output.

    The list of lines from the stdout of the runtime is compared
    against each list of lines in test_out_line_lists. Note that this
    method first checks whether any error was raised during runtime.
    """

    if runtime.raised_exception is not None:
        return CorrectnessResult(complete=True, passed=False, runtime=runtime)

    out_lines = runtime.stdout.strip().split(b"\n")
    passed = any(lines_match(out_lines, test_out_lines) for test_out_lines in test_out_line_lists)

    expected_out_lines = []
    for out_lines in test_out_line_lists:
        expected_out_lines.append(b"\n".join(out_lines).decode(errors="replace"))
    details = dict() if passed else dict(expected=expected_out_lines)

    return CorrectnessResult(passed=passed, runtime=runtime, **details)


def make_make_test_in_out(
        executable_name: str,
        ) -> Callable[..., Callable[[dict], CorrectnessResult]]:
    """Procedurally generate a test case generator (lol).

    The innermost function is the actual test case. The intermediate
    level provides configuration for which input and output paths we
    feed into the executable and compare output to. Lastly, this level
    sets the name of the executable to get from the dependency
    injection system.
    """

    def make_test_in_out(
            test_in_path: Path,
            test_out_path: Path,
            *test_out_paths: Path,
            timeout: float = 1) -> Callable[[dict], CorrectnessResult]:
        """Create an input-output test case.

        Returns a test case that feeds the executable the in path on
        the command line and compares its output to the provided
        options.

        Note that by doing it this way, we read the files on grader
        instantiation instead of every time we want to run the test.
        """

        test_out_line_lists = []
        for out_path in (test_out_path,) + test_out_paths:
            test_out_line_lists.append(out_path.read_bytes().strip().split(b"\n"))

        def test_in_out(resources: dict) -> CorrectnessResult:
            """Actually test the executable."""

            executable = resources[executable_name]
            runtime = executable.execute(str(test_in_path), timeout=timeout)
            return compare_stdout(runtime, test_out_line_lists)

        return test_in_out

    return make_test_in_out


# TODO: make_make can be made into a functools.partial wrapper

def make_exit_test(executable_name: str, *args: str, timeout: float):
    """Make a generic exit code test."""

    def test(resources: dict) -> CorrectnessResult:
        executable = resources[executable_name]
        runtime = executable.execute(*args, timeout=timeout)
        if runtime.error or runtime.code != 0:
            return CorrectnessResult(passed=False, runtime=runtime)
        return CorrectnessResult(passed=True, runtime=runtime)

    return test
