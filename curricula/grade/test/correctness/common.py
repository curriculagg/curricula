import abc

from typing import *
from pathlib import Path

from . import CorrectnessResult
from .. import Test
from ...task import Error
from ....library.process import Runtime, Interactive, InteractiveStreamTimeoutExpired, Interaction
from ....library.introspection import none, not_none

__all__ = (
    "as_lines",
    "lines_match",
    "lines_match_unordered",
    "test_runtime_succeeded",
    "OutputTest",
    "CompareTest",
    "CompareBytesOutputTest",
    "ExecutableMixin",
    "ExecutableInputFileMixin",
    "ExecutableOutputFileMixin",
    "ExecutableExitCodeTest",
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


class CompareBytesOutputTest(OutputTest):
    """Compares output to expected values."""

    def __init__(
            self,
            *,
            out_transform: BytesTransform = identity,
            out_line_transform: BytesTransform = identity,
            test_out: bytes = None,
            test_out_lines: Iterable[bytes] = None,
            test_out_lines_lists: Iterable[Iterable[bytes]] = None,
            **kwargs):
        """Build a test for matching stdout output.

        The list of lines from the stdout of the runtime is compared
        against each list of lines in test_out_line_lists. Note that this
        method first checks whether any error was raised during runtime.
        """

        super().__init__(**kwargs)

        if len(tuple(filter(lambda x: x is not None, (test_out, test_out_lines, test_out_lines_lists)))) != 1:
            raise ValueError("Exactly one of test_out, test_out_lines, or test_out_lines_lists is required")

        if test_out is not None:
            self.test = CompareBytesOutputTest.create_out_test(
                out_transform=out_transform,
                test_out=test_out)
        else:
            if test_out_lines is not None:
                test_out_lines_lists = [test_out_lines]
            self.test = CompareBytesOutputTest.create_out_lines_lists_test(
                out_transform=out_transform,
                out_line_transform=out_line_transform,
                test_out_lines_lists=test_out_lines_lists)

    @classmethod
    def create_out_test(cls, out_transform: BytesTransform, test_out: bytes) -> CompareTest:
        """Shortcut for comparing a single block of text."""

        def test(out: bytes):
            out = out_transform(out)
            passing = out == test_out
            error = None if passing else Error(
                description="unexpected output",
                expected=[test_out.decode(errors="replace")],
                received=out.decode(errors="replace"))
            return CorrectnessResult(passing=passing, error=error)

        return test

    @classmethod
    def create_out_lines_lists_test(
            cls,
            out_transform: BytesTransform,
            out_line_transform: BytesTransform,
            test_out_lines_lists: Iterable[Iterable[bytes]]) -> CompareTest:
        """Used to compare multiple options of lists of lines."""

        expected = [b"\n".join(test_out_lines).decode(errors="replace") for test_out_lines in test_out_lines_lists]

        def test(out: bytes):
            out_lines = tuple(map(out_line_transform, out_transform(out).split(b"\n")))
            passing = any(lines_match(out_lines, lines) for lines in test_out_lines_lists)
            error = None if passing else Error(
                description="unexpected output",
                expected=expected,
                received=b"\n".join(out_lines).decode(errors="replace"))
            return CorrectnessResult(passing=passing, error=error)

        return test


def test_runtime_succeeded(runtime: Runtime) -> CorrectnessResult:
    """See if the runtime raised exceptions or returned status code."""

    if runtime.raised_exception:
        return CorrectnessResult(
            passing=False,
            runtime=runtime.dump(),
            error=Error(description=runtime.exception.description))
    elif runtime.timed_out:
        return CorrectnessResult(
            passing=False,
            runtime=runtime.dump(),
            error=Error(description="timed out",
                        suggestion=f"expected maximum elapsed time of {runtime.timeout} seconds"))
    elif runtime.code != 0:
        return CorrectnessResult(
            passing=False,
            runtime=runtime.dump(),
            error=Error(description=f"received status code {runtime.code}",
                        suggestion="expected status code of zero"))
    return CorrectnessResult(passing=True)


class ExecutableMixin(OutputTest):
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

    def get_args(self) -> Iterable[str]:
        return not_none("args", self.args, default_value=())

    def get_stdin(self) -> Optional[bytes]:
        return not_none("stdin", self.stdin, default_value=None)

    def get_timeout(self) -> Optional[float]:
        return not_none("timeout", self.timeout, default_value=None)

    def get_cwd(self) -> Optional[Path]:
        return not_none("cwd", self.cwd, default_value=None)

    def execute(self) -> Runtime:
        """Check that it ran correctly, then run the test."""

        executable = self.resources[self.executable_name]
        runtime = executable.execute(
            *self.get_args(),
            stdin=self.get_stdin(),
            timeout=self.get_timeout(),
            cwd=self.get_cwd())
        self.details["runtime"] = runtime.dump()
        return runtime

    def get_output(self) -> Any:
        """Return stdout by default."""

        runtime = self.execute()

        # Check standard stuff
        result = test_runtime_succeeded(runtime)
        if not result.passing:
            raise result

        return runtime.stdout

    def get_exit_code(self) -> Any:
        """Return exit code."""

        return self.execute().code


class ExecutableInputFileMixin(OutputTest):
    """Enables the use of an input file rather than stdin string."""

    stdin: bytes
    input_file_path: Path

    def __init__(self, *, input_file_path: Path = none, **kwargs):
        """Set stdin."""

        super().__init__(**kwargs)
        self.input_file_path = input_file_path
        self.stdin = self.get_input_file_path().read_bytes()

    def get_input_file_path(self) -> Path:
        """Override or specify in constructor."""

        return not_none("input_file_path", self.input_file_path)


class ExecutableOutputFileMixin(OutputTest):
    """Enables the use of an input file rather than stdin string."""

    output_file_path: Path

    def __init__(self, *, output_file_path: Path = none, **kwargs):
        """Set stdin."""

        super().__init__(**kwargs)
        self.output_file_path = output_file_path

    def get_output_file_path(self) -> Path:
        """Override or specify in constructor."""

        return not_none("output_file_path", self.output_file_path)

    def get_output(self) -> Any:
        """Call super because it might do something."""

        super().get_output()
        output_file_path = self.get_output_file_path()
        if not output_file_path.is_file():
            raise CorrectnessResult(passing=False, error=Error(
                description="no output file",
                suggestion=f"expected path {output_file_path}"))
        return output_file_path.read_bytes()


ExitCodeTest = Callable[[int], CorrectnessResult]


class ExecutableExitCodeTest(Test, abc.ABC):
    """Checks program exit code."""

    test: ExitCodeTest
    resources: Optional[dict]
    details: Optional[dict]

    def __init__(self, *, expected_code: int = None, expected_codes: Container[int] = None):
        """Set expected codes."""

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
                    description=f"received incorrect exit code",
                    suggestion=f"expected {expected_codes}"))

        self.test = test

    def get_exit_code(self) -> int:
        """Override this."""

        pass

    def __call__(self, resources: dict) -> CorrectnessResult:
        """Check if the output matches."""

        self.resources = resources
        self.details = {}
        result = self.test(self.get_exit_code())
        result.details.update(self.details)
        self.resources = None
        self.details = None
        return result


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
            except InteractiveStreamTimeoutExpired:
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
