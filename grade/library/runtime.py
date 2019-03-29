import subprocess
import timeit
from typing import Optional, Tuple


class Runtime:
    """Runtime data extracted from running an external process."""

    __slots__ = ("timeout", "code", "stdout", "stderr", "elapsed")

    timeout: Optional[float]  # Populated if timed out
    code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    elapsed: Optional[float]

    def __init__(self, *,
                 timeout: float = None,
                 code: int = None,
                 stdout: str = None,
                 stderr: str = None,
                 elapsed: float = None):
        self.timeout = timeout
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed = elapsed


def run(*args: str, timeout: float) -> Runtime:
    """Run an executable with a list of command line arguments.

    The provided path must be absolute in order to properly execute
    the program. Args provided are passed as they would be from the
    command line. The timeout is measured in seconds.
    """

    # Spawn the process, access stdout and stderr
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for the process to finish with timeout
    start = timeit.default_timer()
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        # TODO: include any stdout and stderr that made it into the buffer
        return Runtime(timeout=timeout)
    elapsed = timeit.default_timer() - start

    return Runtime(code=process.returncode, stdout=stdout.decode(), stderr=stderr.decode(), elapsed=elapsed)


class Executable:
    """A runnable testing target program."""

    args: Tuple[str]

    def __init__(self, *args: str):
        """Initialize a target with commands to run the target.

        Any paths invoked in the executable command must be absolute; relative
        requires subprocess configuration that is unsafe.
        """

        self.args = tuple(args)

    def run(self, *args: str, timeout: float) -> Runtime:
        """Run the target with command line arguments."""

        return run(*self.args, *args, timeout=timeout)
