from typing import List, Iterable, AnyStr, Union, Sized, Callable
from pathlib import Path

from . import CorrectnessResult
from ....library.process import Runtime

__all__ = (
    "as_lines",
    "lines_match",
    "make_stdout_test",
    "make_make_test_in_out",
    "make_exit_test",
    "wrap_runtime_test")


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


BytesTransform = Callable[[bytes], bytes]
RuntimeTest = Callable[[Runtime], CorrectnessResult]


def identity(x):
    return x


def make_stdout_test(
        *,
        out_transform: BytesTransform = identity,
        out_line_transform: BytesTransform = identity,
        test_out: bytes = None,
        test_out_lines: List[bytes] = None,
        test_out_lines_lists: List[List[bytes]] = None) -> RuntimeTest:
    """Build a test for matching stdout output.

    The list of lines from the stdout of the runtime is compared
    against each list of lines in test_out_line_lists. Note that this
    method first checks whether any error was raised during runtime.
    """

    if len(tuple(filter(None, (test_out, test_out_lines, test_out_lines_lists)))) != 1:
        raise ValueError("Exactly one of test_out, test_out_lines, or test_out_lines_lists is required")

    if test_out is not None:
        def compare_stdout(runtime: Runtime):
            """Direct comparision of output."""

            out = out_transform(runtime.stdout)
            passed = out == test_out
            details = {} if passed else {"expected": [test_out.decode(errors="replace")]}
            return CorrectnessResult(passed=passed, runtime=runtime.dump(), **details)
        return compare_stdout

    else:
        if test_out_lines is not None:
            test_out_lines_lists = [test_out_lines]
        expected_out = []
        for expected_lines in test_out_lines_lists:
            expected_out.append(b"\n".join(expected_lines).decode(errors="replace"))

        def compare_stdout(runtime: Runtime):
            """Compare by line."""

            out_lines = tuple(map(out_line_transform, out_transform(runtime.stdout).split(b"\n")))
            passed = any(lines_match(out_lines, lines) for lines in test_out_lines_lists)
            details = dict() if passed else dict(expected=expected_out)
            return CorrectnessResult(passed=passed, runtime=runtime.dump(), **details)
        return compare_stdout


def make_test_in_out(
        executable_name: str,
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

    test_out_lines_lists = []
    for out_path in (test_out_path,) + test_out_paths:
        test_out_lines_lists.append(out_path.read_bytes().strip().split(b"\n"))
    compare_stdout = make_stdout_test(test_out_lines_lists=test_out_lines_lists)

    def test_in_out(resources: dict) -> CorrectnessResult:
        """Actually test the executable."""

        executable = resources[executable_name]
        runtime = executable.execute(str(test_in_path), timeout=timeout)
        return compare_stdout(runtime)

    return test_in_out


def make_exit_test(executable_name: str, *args: str, timeout: float = None):
    """Make a generic exit code test."""

    def test(resources: dict) -> CorrectnessResult:
        executable = resources[executable_name]
        runtime: Runtime = executable.execute(*args, timeout=timeout)
        if runtime.raised_exception or runtime.code != 0:
            return CorrectnessResult(passed=False, runtime=runtime.dump())
        return CorrectnessResult(passed=True, runtime=runtime.dump())

    return test


def wrap_runtime_test(executable_name: str, *args: str, runtime_test: RuntimeTest, timeout: float = None):
    """Make a simple stdout test."""

    def test(resources: dict) -> CorrectnessResult:
        executable = resources[executable_name]
        runtime = executable.execute(*args, timeout=timeout)
        if runtime.raised_exception:
            return CorrectnessResult(passed=False, runtime=runtime.dump(), error=runtime.exception.description)
        elif runtime.timed_out:
            return CorrectnessResult(passed=False, runtime=runtime.dump(), error="timed out")
        elif runtime.code != 0:
            return CorrectnessResult(passed=False, runtime=runtime.dump(), error="expected status code of zero")
        return runtime_test(runtime)

    return test
