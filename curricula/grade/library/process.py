import subprocess
import timeit
from typing import Optional, Tuple
from dataclasses import dataclass, asdict


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
        dump = asdict(self)
        for field in "stdout", "stdin", "stderr":
            if dump[field] is not None:
                dump[field] = dump[field].decode(errors="replace")
        return dump


def run(*args: str, stdin: bytes = None, timeout: float = None) -> Runtime:
    """Run an executable with a list of command line arguments.

    The provided path must be absolute in order to properly execute
    the program. Args provided are passed as they would be from the
    command line. The timeout is measured in seconds.
    """

    # Spawn the process, access stdout and stderr
    try:
        if stdin:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        else:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Catch common errors
    except OSError as error:
        exception = RuntimeException(
            description="executable format error" if error.errno == 8 else "failed to run executable",
            error_number=error.errno)
        return Runtime(args=args, timeout=timeout, stdin=stdin, raised_exception=True, exception=exception)
    except ValueError:
        exception = RuntimeException(description="failed to open process")
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
