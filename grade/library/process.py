import subprocess
import timeit
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class Runtime:
    """Runtime data extracted from running an external process."""

    command: str
    timeout: Optional[float]  # Populated if timed out
    code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    elapsed: Optional[float]

    def __init__(self,
                 command: str,
                 *,
                 timeout: float = None,
                 code: int = None,
                 stdout: str = None,
                 stderr: str = None,
                 elapsed: float = None):
        self.command = command
        self.timeout = timeout
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed = elapsed

    def dump(self) -> dict:
        return asdict(self)


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
        return Runtime(" ".join(args), timeout=timeout)
    elapsed = timeit.default_timer() - start

    return Runtime(" ".join(args),
                   code=process.returncode,
                   stdout=stdout.decode(),
                   stderr=stderr.decode(),
                   elapsed=elapsed)
