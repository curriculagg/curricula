import subprocess
import timeit
import os
from typing import Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field


@dataclass(eq=False)
class RuntimeException:
    """Error that occurs during process runtime."""

    description: str
    error_number: Optional[int] = None


@dataclass(eq=False)
class Runtime:
    """Runtime data extracted from running an external process."""

    args: Tuple[str]
    timeout: float  # Populated if timed out

    code: Optional[int] = None
    elapsed: Optional[float] = None
    stdin: Optional[bytes] = None
    stdout: Optional[bytes] = None
    stderr: Optional[bytes] = None

    timed_out: bool = False
    raised_exception: bool = False
    exception: Optional[RuntimeException] = None

    def dump(self) -> dict:
        """Make the runtime JSON serializable."""

        dump = asdict(self)
        for field_name in "stdout", "stdin", "stderr":
            if dump[field_name] is not None:
                dump[field_name] = dump[field_name].decode(errors="replace")
        return dump


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


def run(*args: str, stdin: bytes = None, timeout: float = None) -> Runtime:
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
                preexec_fn=config.process_setup)
        else:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=config.process_setup)

    # Catch common errors
    except OSError as error:
        exception = RuntimeException(
            description="executable format error" if error.errno == 8 else "failed to run executable",
            error_number=error.errno)
        return Runtime(args=args, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)
    except ValueError:
        exception = RuntimeException(description="failed to open process")
        return Runtime(args=args, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)
    except subprocess.SubprocessError as exception:
        exception = RuntimeException(description=str(exception))
        return Runtime(args=args, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)

    # Wait for the process to finish with timeout
    start = timeit.default_timer()
    try:
        stdout, stderr = process.communicate(input=stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        return Runtime(args=args, timeout=timeout, stdin=stdin, stdout=stdout, stderr=stderr, timed_out=True)

    # Check elapsed
    elapsed = timeit.default_timer() - start
    return Runtime(
        args=args,
        timeout=timeout,
        code=process.returncode,
        elapsed=elapsed,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr)
