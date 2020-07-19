import subprocess
import timeit
import time

from typing import Optional, Tuple, Callable, IO, TypeVar, Any
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path


@dataclass(eq=False)
class ProcessError:
    """Error that occurs during process runtime."""

    description: str
    error_number: Optional[int] = None

    @classmethod
    def from_os_error(cls, error: OSError) -> "ProcessError":
        """Create from OS error."""

        if error.errno == 8:
            description = "executable format error"
        else:
            description = "failed to run executable"

        return ProcessError(description=description, error_number=error.errno)

    def dump(self) -> dict:
        """Serialize."""

        return asdict(self)


T = TypeVar("T")


@lru_cache(maxsize=None)
def nullable(function: Callable[[Any], T]) -> Callable[[Optional[Any]], Optional[T]]:
    """None should pass through."""

    return lambda value: function(value) if value is not None else None


@dataclass(eq=False)
class ProcessCreation:
    """Information about how a process was started."""

    args: Tuple[str, ...]
    cwd: Optional[Path]

    def dump(self) -> dict:
        """Simple serialization."""

        dump = getattr(super(), "dump", dict)()
        dump.update(
            args=self.args,
            cwd=nullable(str)(self.cwd))
        return dump


@dataclass(eq=False)
class ProcessStreams:
    """Container for streamed data."""

    stdin: Optional[bytes] = None
    stdout: Optional[bytes] = None
    stderr: Optional[bytes] = None

    def dump(self) -> dict:
        """Decode any stream data from bytes."""

        dump = getattr(super(), "dump", dict)()
        dump.update(
            stdin=nullable(bytes.decode)(self.stdin),
            stdout=nullable(bytes.decode)(self.stdout),
            stderr=nullable(bytes.decode)(self.stderr))
        return dump


@dataclass(eq=False)
class Interaction(ProcessStreams, ProcessCreation):
    """Container for single interaction with a process."""

    elapsed: Optional[float] = None

    def dump(self) -> dict:
        """Make the runtime JSON serializable."""

        dump = super().dump()
        dump.update(elapsed=self.elapsed)
        return dump


@dataclass(eq=False)
class Runtime(ProcessStreams, ProcessCreation):
    """Runtime data extracted from running an external process."""

    # Elapsed time to finish
    elapsed: Optional[float] = None

    # A process must terminate one of three ways
    code: Optional[int] = None

    # Timeout to avoid hanging indefinitely
    timeout: Optional[float] = None
    timed_out: bool = False

    # Exception preventing start
    raised_exception: bool = False
    exception: Optional[ProcessError] = None


@dataclass(eq=False)
class TimeoutExpired(RuntimeError):
    """Raised waiting for process termination or blocking I/O."""

    # Any extra data in the buffer
    buffer: bytes


@dataclass(eq=False)
class Stream:
    """Base class for a process stream wrapper."""

    file: IO[bytes]

    # Track all data passed through stream
    history: bytes = field(init=False, default=b"")


@dataclass(eq=False)
class Readable(Stream):
    """Custom IO stream for Interactive."""

    # Poll rate for reading
    POLL: float = 0.001

    def _read_block(self, condition: Callable[[bytes], bool] = None, timeout: float = None) -> Optional[bytes]:
        """Block until something besides None is returned."""

        buffer = b""

        timeout_time = None
        if timeout is not None:
            timeout_time = timeit.default_timer() + timeout

        while True:
            data = self.file.read()
            if data is not None:
                buffer += data
                if condition is None or condition(buffer):
                    break
            if timeout is not None and timeit.default_timer() >= timeout_time:
                self.history += buffer
                raise TimeoutExpired(buffer=buffer)
            time.sleep(self.POLL)

        self.history += buffer
        return buffer

    def read(
            self,
            condition: Callable[[bytes], bool] = None,
            timeout: float = None) -> Optional[bytes]:
        """Read from a stream.

        If blocking is disabled, may return None. If condition is not
        None, block until condition is satisfied. If timeout is not
        None, break after timeout and return buffer or None.
        """

        return self._read_block(condition=condition, timeout=timeout)


@dataclass(eq=False)
class Writable(Stream):
    """Provides a print-like wrapper for an output stream."""

    def write(
            self,
            *values: bytes,
            sep: bytes = b" ",
            end: bytes = b"\n",
            flush: bool = True):
        """Write to the stream like traditional print."""

        data = sep.join(values) + end
        self.file.write(data)
        self.history += data
        if flush:
            try:
                self.file.flush()
            except BrokenPipeError:
                pass


@dataclass(eq=False)
class Interactive:
    """An interactive runtime session."""

    _args: Tuple[str, ...]
    _process: subprocess.Popen
    _start_time: float
    cwd: Optional[Path]
    stdin: Writable
    stdout: Readable
    stderr: Readable

    _recording: Optional[Interaction] = None

    def __init__(self, args: Tuple[str, ...], cwd: Path = None):
        """Start up the new process."""

        self._args = args
        self._process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            cwd=str(cwd) if cwd is not None else None)
        self.cwd = cwd
        self.stdin = Writable(self._process.stdin)
        self.stdout = Readable(self._process.stdout)
        self.stderr = Readable(self._process.stderr)
        self._start_time = timeit.default_timer()

    def poll(self) -> bool:
        """Check whether the interactive has terminated."""

        return self._process.poll() is None

    @contextmanager
    def recording(self) -> Interaction:
        """Record a frame of all process streams."""

        if self._recording is not None:
            raise RuntimeError("Cannot make multiple runtime recordings at once!")

        partial = Interaction(args=self._args, cwd=self.cwd)
        stdin_index = len(self.stdin.history)
        stdout_index = len(self.stdout.history)
        stderr_index = len(self.stderr.history)
        start_time = timeit.default_timer()

        yield partial

        # Collect everything that changed
        partial.elapsed = timeit.default_timer() - start_time
        partial.stdin = self.stdin.history[stdin_index:]
        partial.stdout = self.stdout.history[stdout_index:]
        partial.stderr = self.stderr.history[stderr_index:]

    def close(self, timeout: float = None) -> Runtime:
        """Block until exit."""

        raised_exception = False
        exception = None
        timed_out = False
        stdout = b""
        stderr = b""

        try:
            stdout, stderr = self._process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        except OSError as error:
            raised_exception = True
            exception = ProcessError.from_os_error(error)

        stop_time = timeit.default_timer()
        return Runtime(
            args=self._args,
            cwd=self.cwd,
            timeout=timeout,
            code=self._process.returncode,
            elapsed=stop_time - self._start_time,
            stdin=self.stdin.history,
            stdout=self.stdout.history + stdout,
            stderr=self.stderr.history + stderr,
            raised_exception=raised_exception,
            exception=exception,
            timed_out=timed_out)


def run(*args: str, stdin: bytes = None, timeout: float = None, cwd: Path = None) -> Runtime:
    """Run an executable with a list of command line arguments.

    The provided path must be absolute in order to properly execute
    the program. Args provided are passed as they would be from the
    command line. The timeout is measured in seconds.

    The process_setup callable is invoked within the spawned process
    prior to the execution of the command.
    """

    # Spawn the process, access stdout and stderr
    try:
        if stdin is not None:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=str(cwd) if cwd is not None else None)
        else:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd) if cwd is not None else None)

    # Catch common errors
    except OSError as error:
        exception = ProcessError.from_os_error(error)
        return Runtime(args=args, cwd=cwd, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)
    except ValueError:
        exception = ProcessError(description="failed to open process")
        return Runtime(args=args, cwd=cwd, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)
    except subprocess.SubprocessError as exception:
        exception = ProcessError(description=str(exception))
        return Runtime(args=args, cwd=cwd, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)

    # Wait for the process to finish with timeout
    start = timeit.default_timer()
    try:
        stdout, stderr = process.communicate(input=stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()

        # Recover data
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            stdout, stderr = None, None

        return Runtime(args=args, cwd=cwd, timeout=timeout, stdin=stdin, stdout=stdout, stderr=stderr, timed_out=True)

    # Check elapsed
    elapsed = timeit.default_timer() - start
    return Runtime(
        args=args,
        cwd=cwd,
        timeout=timeout,
        code=process.returncode,
        elapsed=elapsed,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr)


def interact(*args: str) -> Interactive:
    """Shorthand for interactive, makes the interface nicer."""

    return Interactive(args=args)
