import subprocess
import timeit
from typing import Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass(eq=False)
class Runtime:
    """Runtime data extracted from running an external process."""

    args: Tuple[str]
    timeout: float  # Populated if timed out

    elapsed: Optional[float] = None
    code: Optional[int] = None
    stdout: Optional[bytes] = None
    stderr: Optional[bytes] = None

    timed_out: bool = False
    raised_exception: bool = False
    exception: Optional[str] = None

    def dump(self) -> dict:
        dump = asdict(self)
        if self.stdout is not None:
            dump["stdout"] = self.stdout.decode(errors="replace")
        if self.stderr is not None:
            dump["stderr"] = self.stderr.decode(errors="replace")
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
        exception = "executable format error" if error.errno == 8 else "failed to run executable"
        return Runtime(args=args, timeout=timeout, raised_exception=True, exception=exception)
    except ValueError:
        exception = "failed to open process"
        return Runtime(args=args, timeout=timeout, raised_exception=True, exception=exception)

    # Wait for the process to finish with timeout
    start = timeit.default_timer()
    try:
        stdout, stderr = process.communicate(input=stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=timeout)
        return Runtime(args=args, timeout=timeout, stdout=stdout, stderr=stderr, timed_out=True)

    # Check elapsed
    elapsed = timeit.default_timer() - start
    return Runtime(args=args, timeout=timeout, code=process.returncode, stdout=stdout, stderr=stderr, elapsed=elapsed)
