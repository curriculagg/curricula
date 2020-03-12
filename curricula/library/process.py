import subprocess
import timeit
import os
import time
import signal

try:
    import fcntl
except ImportError:
    fcntl = None

from typing import Optional, Tuple, Callable, IO
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
from pathlib import Path


@dataclass(eq=False)
class RuntimeException:
    """Error that occurs during process runtime."""

    description: str
    error_number: Optional[int] = None

    @classmethod
    def from_os_error(cls, error: OSError) -> "RuntimeException":
        """Create from OS error."""

        return RuntimeException(
            description="executable format error" if error.errno == 8 else "failed to run executable",
            error_number=error.errno)

    def dump(self) -> dict:
        """Serialize."""

        return asdict(self)


@dataclass(eq=False)
class Interaction:
    """Container for single interaction with a process."""

    args: Tuple[str, ...]
    cwd: Optional[Path]

    elapsed: Optional[float] = None
    stdin: Optional[bytes] = None
    stdout: Optional[bytes] = None
    stderr: Optional[bytes] = None

    def dump(self) -> dict:
        """Make the runtime JSON serializable."""

        dump = asdict(self)
        for field_name in "stdout", "stdin", "stderr":
            if dump[field_name] is not None:
                dump[field_name] = dump[field_name].decode(errors="replace")
        if dump["cwd"]:
            dump["cwd"] = str(dump["cwd"])
        return dump


@dataclass(eq=False)
class Runtime(Interaction):
    """Runtime data extracted from running an external process."""

    code: Optional[int] = None

    timeout: Optional[float] = None
    timed_out: bool = False

    raised_exception: bool = False
    exception: Optional[RuntimeException] = None


class InteractiveStreamTimeoutExpired(RuntimeError):
    buffer: bytes

    def __init__(self, buffer: bytes):
        self.buffer = buffer


class InteractiveStream:
    """Custom IO stream for Interactive."""

    file: IO[bytes]
    history: bytes

    POLL: float = 0.001

    def __init__(self, file: IO[bytes], read: bool, write: bool):
        """Create the stream."""

        self.file = file
        self.history = b""

        if read:
            self._set_nonblock()

        # Disable methods
        if not read:
            self.read = None
        if not write:
            self.write = None

    def _set_nonblock(self):
        """Disable blocking for read."""

        flags = fcntl.fcntl(self.file, fcntl.F_GETFL)
        fcntl.fcntl(self.file, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def _read_nonblock(self) -> Optional[bytes]:
        """Read or return None if no data."""

        data = self.file.read()
        if data is not None:
            self.history += data
        return data

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
                raise InteractiveStreamTimeoutExpired(buffer=buffer)
            time.sleep(self.POLL)

        self.history += buffer
        return buffer

    def read(
            self,
            block: bool = True,
            condition: Callable[[bytes], bool] = None,
            timeout: float = None) -> Optional[bytes]:
        """Read from a stream.

        If blocking is disabled, may return None. If condition is not
        None, block until condition is satisfied. If timeout is not
        None, break after timeout and return buffer or None.
        """

        if block:
            return self._read_block(condition=condition, timeout=timeout)
        return self._read_nonblock()

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
    stdin: InteractiveStream
    stdout: InteractiveStream
    stderr: InteractiveStream

    _recording: Optional[Interaction] = None

    def __init__(self, args: Tuple[str, ...], cwd: Path = None):
        """Start up the new process."""

        self._args = args
        self._process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            preexec_fn=config.process_setup,
            cwd=str(cwd) if cwd is not None else None)
        self.cwd = cwd
        self.stdin = InteractiveStream(self._process.stdin, read=False, write=True)
        self.stdout = InteractiveStream(self._process.stdout, read=True, write=False)
        self.stderr = InteractiveStream(self._process.stdout, read=True, write=False)
        self._start_time = timeit.default_timer()

    def poll(self) -> bool:
        """Check whether the interactive has terminated."""

        return self._process.poll() is None

    @contextmanager
    def recording(self) -> Interaction:
        """Record a frame of all process streams."""

        if self._recording is not None:
            raise RuntimeError("Cannot make multiple runtime recordings at once!")

        partial = Interaction(args=self._args)
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
            exception = RuntimeException.from_os_error(error)

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


def demote_user(user_uid: int, user_gid: int):
    """Set the user of the process."""

    os.setgid(user_gid)
    os.setuid(user_uid)


@dataclass(eq=False)
class SubprocessConfiguration:
    """Global settings."""

    custom_process_setup: Optional[Callable[[], None]] = None

    demote_user_enabled: bool = False
    demote_user_uid: int = field(init=False)
    demote_user_gid: int = field(init=False)

    def set_custom_process_setup(self, custom_process_setup: Callable[[], None]):
        """Can be used as a decorator."""

        self.custom_process_setup = custom_process_setup

    def clear_custom_process_setup(self):
        """Return to default."""

        self.custom_process_setup = None

    def enable_demote_user(self, uid: int, gid: int):
        """Globally enable user demotion in run."""

        self.demote_user_enabled = True
        self.demote_user_uid = uid
        self.demote_user_gid = gid

    def disable_demote_user(self):
        """Globally disable user demotion."""

        self.demote_user_enabled = False

    def process_setup(self):
        """Do not overwrite."""

        if self.custom_process_setup is not None:
            self.custom_process_setup()
        if self.demote_user_enabled:
            demote_user(self.demote_user_uid, self.demote_user_gid)


config = SubprocessConfiguration()


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
                preexec_fn=config.process_setup,
                cwd=str(cwd) if cwd is not None else None)
        else:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=config.process_setup,
                cwd=str(cwd) if cwd is not None else None)

    # Catch common errors
    except OSError as error:
        exception = RuntimeException.from_os_error(error)
        return Runtime(args=args, cwd=cwd, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)
    except ValueError:
        exception = RuntimeException(description="failed to open process")
        return Runtime(args=args, cwd=cwd, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)
    except subprocess.SubprocessError as exception:
        exception = RuntimeException(description=str(exception))
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


def interactive(*args: str) -> Interactive:
    return Interactive(args=args)
