import abc

from typing import *
from pathlib import Path

from . import CorrectnessResult
from .. import Test
from ...task import Error
from ....library.process import Runtime, Interactive, TimeoutExpired, Interaction
from ....library.configurable import none, not_none, Configurable

__all__ = (
    "as_lines",
    "lines_match",
    "lines_match_unordered",
    "test_runtime_succeeded",
    "OutputTest",
    "CompareTest",
    "CompareBytesOutputTest",
    "ExecutableMixin",
    "ExecutableCodeMixin",
    "ExecutableInputFileMixin",
    "ExecutableOutputFileMixin",
    "CompareExitCodeOutputTest",
    "write_then_read")


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


CompareTest = Callable[[Any], CorrectnessResult]


class OutputTest(Test, abc.ABC):
    """Compares program output to an expected output."""

    test: CompareTest
    resources: Optional[dict]
    details: Optional[dict]

    def __init__(self, **kwargs):
        """Create shared fields."""

        if len(kwargs) > 0:
            raise SyntaxError(f"base class received kwargs {kwargs.keys()}")

    def get_output(self) -> Any:
        """Override this."""

        pass

    def __call__(self, resources: dict) -> CorrectnessResult:
        """Check if the output matches."""

        self.resources = resources
        self.details = {}
        result = self.test(self.get_output())
        result.details.update(self.details)
        self.resources = None
        self.details = None
        return result


BytesTransform = Callable[[bytes], bytes]
T = TypeVar("T")


def identity(x: T) -> T:
    return x


class CompareBytesOutputTest(OutputTest, Configurable):
    """Compares output to expected values."""

    out_transform: BytesTransform
    out_line_transform: BytesTransform
    test_out: bytes
    test_out_lines: Iterable[bytes]
    test_out_lines_lists: Iterable[Iterable[bytes]]

    def __init__(
            self,
            *,
            out_transform: BytesTransform = none,
            out_line_transform: BytesTransform = none,
            test_out: bytes = none,
            test_out_lines: Iterable[bytes] = none,
            test_out_lines_lists: Iterable[Iterable[bytes]] = none,
            **kwargs):
        """Build a test for matching stdout output.

        The list of lines from the stdout of the runtime is compared
        against each list of lines in test_out_line_lists. Note that this
        method first checks whether any error was raised during runtime.
        """

        super().__init__(**kwargs)
        self.test_out = self.resolve("test_out", local=test_out, default=None)
        self.test_out_lines = self.resolve("test_out_lines", local=test_out_lines, default=None)
        self.test_out_lines_lists = self.resolve("test_out_lines_lists", local=test_out_lines_lists, default=None)

        # Check resolvable
        resolvable = tuple(filter(None, (self.test_out, self.test_out_lines, self.test_out_lines_lists)))
        if len(resolvable) != 1:
            raise ValueError("Exactly one of test_out, test_out_lines, or test_out_lines_lists is required")

        self.out_transform = self.resolve("out_transform", local=out_transform, default=identity)
        self.out_line_transform = self.resolve("out_line_transform", local=out_line_transform, default=identity)

    def test(self, out: bytes):
        """Call the corresponding test."""

        if self.test_out is not None:
            return self._test_out(out)
        return self._test_out_lines_lists(out)

    def _test_out(self, out: bytes) -> CorrectnessResult:
        """Shortcut compare for one option block text."""

        test_out = self.resolve("test_out")

        out = self.out_transform(out)
        passing = out == test_out
        error = None if passing else Error(
            description="unexpected output",
            expected=test_out.decode(errors="replace"),
            received=out.decode(errors="replace"))
        return CorrectnessResult(passing=passing, error=error)

    def _test_out_lines_lists(self, out: bytes) -> CorrectnessResult:
        """Used to compare multiple options of lists of lines."""

        if self.test_out_lines is not None:
            test_out_lines_lists = [self.test_out_lines]
        else:
            test_out_lines_lists = self.test_out_lines_lists

        out_lines = tuple(map(self.out_line_transform, self.out_transform(out).split(b"\n")))
        passing = any(lines_match(out_lines, lines) for lines in test_out_lines_lists)
        expected = tuple(b"\n".join(test_out_lines).decode(errors="replace") for test_out_lines in test_out_lines_lists)
        error = None if passing else Error(
            description="unexpected output",
            expected=expected[0] if len(expected) == 1 else expected,
            received=b"\n".join(out_lines).decode(errors="replace"))
        return CorrectnessResult(passing=passing, error=error)


def test_runtime_succeeded(runtime: Runtime) -> CorrectnessResult:
    """See if the runtime raised exceptions or returned status code."""

    if runtime.raised_exception:
        error = Error(description=runtime.exception.description)
        raise CorrectnessResult(passing=False, runtime=runtime.dump(), error=error)
    if runtime.timed_out:
        error = Error(
            description="timed out",
            suggestion=f"expected maximum elapsed time of {runtime.timeout} seconds")
        raise CorrectnessResult(passing=False, runtime=runtime.dump(), error=error)
    if runtime.code != 0:
        error = Error(
            description=f"received status code {runtime.code}",
            suggestion="expected status code of zero")
        return CorrectnessResult(passing=False, runtime=runtime.dump(), error=error)


class ExecutableMixin(OutputTest, Configurable):
    """Meant for reading and comparing stdout."""

    executable_name: str
    args: Iterable[str]
    stdin: Optional[bytes]
    timeout: Optional[float]
    cwd: Optional[Path]

    def __init__(
            self,
            *,
            executable_name: str = none,
            args: Iterable[str] = none,
            stdin: bytes = none,
            timeout: float = none,
            cwd: Path = none,
            **kwargs):
        """Save container information, call super."""

        super().__init__(**kwargs)
        self.executable_name = executable_name
        self.args = args
        self.stdin = stdin
        self.timeout = timeout
        self.cwd = cwd

    def execute(self) -> Runtime:
        """Check that it ran correctly, then run the test."""

        executable = self.resources[self.executable_name]
        runtime = executable.execute(
            *self.resolve("args", default=()),
            stdin=self.resolve("stdin", default=None),
            timeout=self.resolve("timeout", default=None),
            cwd=self.resolve("cwd", default=None))
        self.details["runtime"] = runtime.dump()
        return runtime

    def get_output(self) -> Any:
        """Return stdout by default."""

        runtime = self.execute()
        test_runtime_succeeded(runtime)
        return runtime.stdout


class ExecutableCodeMixin(ExecutableMixin):
    """Output is exit code instead of stdout."""

    def get_output(self) -> Any:
        """Return exit code."""

        return self.execute().code


class ExecutableInputFileMixin(OutputTest, Configurable):
    """Enables the use of an input file rather than stdin string."""

    stdin: bytes
    input_file_path: Path

    def __init__(self, *, input_file_path: Path = none, **kwargs):
        """Set stdin."""

        super().__init__(**kwargs)
        self.input_file_path = input_file_path
        self.stdin = self.resolve("input_file_path").read_bytes()


class ExecutableOutputFileMixin(OutputTest, Configurable):
    """Enables the use of an input file rather than stdin string."""

    output_file_path: Path

    def __init__(self, *, output_file_path: Path = none, **kwargs):
        """Set stdin."""

        super().__init__(**kwargs)
        self.output_file_path = output_file_path

    def get_output(self) -> Any:
        """Call super because it might do something."""

        super().get_output()
        output_file_path = self.resolve("output_file_path")
        if not output_file_path.is_file():
            raise CorrectnessResult(passing=False, error=Error(
                description="no output file",
                suggestion=f"expected path {output_file_path}"))
        return output_file_path.read_bytes()


CompareNativeTest = Callable[[Any], CorrectnessResult]


class CompareExitCodeOutputTest(OutputTest, Configurable):
    """Checks program exit code."""

    test: CompareNativeTest
    resources: Optional[dict]
    details: Optional[dict]

    expected_code: int
    expected_codes: Container[int]

    def __init__(self, *, expected_code: int = none, expected_codes: Container[int] = none, **kwargs):
        """Set expected codes."""

        super().__init__(**kwargs)

        expected_code = self.resolve("expected_code", local=expected_code, default=None)
        expected_codes = self.resolve("expected_codes", local=expected_codes, default=None)

        if expected_code is None and expected_codes is None:
            raise ValueError("Runtime exit test requires either expected status or statuses!")
        if expected_code is not None:
            expected_codes = (expected_code,)

        def test(code: int):
            if code in expected_codes:
                return CorrectnessResult(passing=True)
            return CorrectnessResult(
                passing=False,
                error=Error(
                    description=f"received incorrect exit code f{code}",
                    suggestion=f"expected {expected_codes}"))

        self.test = test


def write_then_read(
        interactive: Interactive,
        stdin: Sequence[bytes],
        read_condition: Callable[[bytes], bool] = None,
        read_condition_timeout: float = None) -> Interaction:
    """Pass in a bunch of lines, get the last output, compare."""

    if not interactive.poll():
        raise CorrectnessResult(passing=False, error=Error(description="program crashed"))

    with interactive.recording() as interaction:
        for command in stdin:
            interactive.stdin.write(command)
            try:
                interactive.stdout.read(
                    block=True,
                    condition=read_condition,
                    timeout=read_condition_timeout)
            except TimeoutExpired:
                raise CorrectnessResult(
                    passing=False,
                    error=Error(description="timed out"),
                    runtime=interaction.dump())

    if interaction.stdout is None:
        raise CorrectnessResult(
            passing=False,
            error=Error(description="did not receive output"),
            runtime=interaction.dump())

    return interaction
