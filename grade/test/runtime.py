import subprocess
import timeit
from typing import Optional, Tuple


class Runtime:
    """Runtime data extracted from running an external process."""

    hang: bool
    timeout: float

    code: Optional[int]
    stdout: Optional[bytes]
    stderr: Optional[bytes]
    elapsed: Optional[float]

    def __init__(self, hang: bool, timeout: float,
                 code: int = None, stdout: bytes = None, stderr: bytes = None, elapsed: float = None):
        self.hang = hang
        self.timeout = timeout
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed = elapsed


def run(*args: str, timeout: float = None) -> Runtime:
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
        stdout, stderr = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        return Runtime(True, timeout)
    elapsed = timeit.default_timer() - start

    return Runtime(False, timeout, process.returncode, stdout, stderr, elapsed)


class Target:
    """A runnable testing target program."""

    executable: Tuple[str]

    def __init__(self, *executable: str):
        """Initialize a target with commands to run the target.

        Any paths invoked in the executable command must be absolute; relative
        requires subprocess configuration that is unsafe.
        """

        self.executable = tuple(executable)

    def run(self, *args: str, timeout: float = None) -> Runtime:
        """Run the target with command line arguments."""

        return run(*self.executable, *args, timeout=timeout)
