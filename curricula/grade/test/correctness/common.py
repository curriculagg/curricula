import functools

from typing import List, Iterable, AnyStr, Union, Sized, Callable, Container, TypeVar
from pathlib import Path

from . import CorrectnessResult
from ....library.process import Runtime

__all__ = (
    "as_lines",
    "lines_match",
    "lines_match_test",
    "test_runtime_succeeded",
    "make_stdout_runtime_test",
    "make_in_out_test",
    "make_exit_runtime_test",
    "wrap_runtime_test",
    "make_exit_zero")


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


def lines_match_unordered(a: AnyStrSequence, b: AnyStrSequence) -> bool:
    """Check unordered equality."""

    return lines_match(sorted(a), sorted(b))


def lines_match_test(
        a: Iterable[bytes],
        b: Iterable[bytes],
        ordered: bool = True,
        **details: dict) -> CorrectnessResult:
    """Wrap lines match with correctness result."""

    match = lines_match if ordered else lines_match_unordered
    if match(a, b):
        return CorrectnessResult(passed=True, **details)
    return CorrectnessResult(
        passed=False,
        received=b"\n".join(a).decode() + "\n",
        expected=b"\n".join(b).decode() + "\n",
        **details)


BytesTransform = Callable[[bytes], bytes]
RuntimeTest = Callable[[Runtime], CorrectnessResult]
T = TypeVar("T")


def identity(x: T) -> T:
    return x


def test_runtime_succeeded(runtime: Runtime) -> CorrectnessResult:
    """See if the runtime raised exceptions or returned status code."""

    if runtime.raised_exception:
        return CorrectnessResult(passed=False, runtime=runtime.dump(), error=runtime.exception.description)
    elif runtime.timed_out:
        return CorrectnessResult(passed=False, runtime=runtime.dump(), error="timed out")
    elif runtime.code != 0:
        return CorrectnessResult(passed=False, runtime=runtime.dump(), error="expected status code of zero")
    return CorrectnessResult(passed=True)


def make_in_out_test(
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
    compare_stdout = make_stdout_runtime_test(test_out_lines_lists=test_out_lines_lists)

    def test_in_out(resources: dict) -> CorrectnessResult:
        """Actually test the executable."""

        executable = resources[executable_name]
        runtime = executable.execute(str(test_in_path), timeout=timeout)

        # Test failed
        runtime_succeeded = test_runtime_succeeded(runtime)
        if not runtime_succeeded.passed:
            return runtime_succeeded

        return compare_stdout(runtime)

    return test_in_out


def make_stdout_runtime_test(
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

    if len(tuple(filter(lambda x: x is not None, (test_out, test_out_lines, test_out_lines_lists)))) != 1:
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


def make_exit_runtime_test(
        *,
        expected_code: int = None,
        expected_codes: Container[int] = None) -> RuntimeTest:
    """Make a generic exit code test."""

    if expected_code is None and expected_codes is None:
        raise ValueError("Runtime exit test requires either expected status or statuses!")
    if expected_code is not None:
        expected_codes = (expected_code,)

    def test(runtime: Runtime) -> CorrectnessResult:
        return CorrectnessResult(passed=runtime.code in expected_codes, runtime=runtime.dump())

    return test


def wrap_runtime_test(
        *,
        executable_name: str,
        args: Iterable[str] = (),
        runtime_test: RuntimeTest,
        stdin: bytes = None,
        timeout: float = None,
        cwd: Path = None):
    """Make a simple stdout test."""

    def test(resources: dict) -> CorrectnessResult:
        executable = resources[executable_name]
        runtime = executable.execute(*args, stdin=stdin, timeout=timeout, cwd=cwd)

        # Check fail
        runtime_succeeded = test_runtime_succeeded(runtime)
        if not runtime_succeeded.passed:
            return runtime_succeeded

        return runtime_test(runtime)

    return test


exit_zero = functools.partial(wrap_runtime_test, runtime_test=make_exit_runtime_test(expected_code=0))


def make_exit_zero(executable_name: str, args: Iterable[str] = (), stdin: bytes = None, timeout: float = None):
    """Make a test that checks if the program returns zero."""

    return exit_zero(executable_name=executable_name, args=args, stdin=stdin, timeout=timeout)
