from typing import Callable, Iterable
from pathlib import Path

from ..task import Error
from . import SetupResult
from ...library.process import TimeoutExpired


def make_open_interactive(
        executable_name: str,
        count: int,
        args: Iterable[str] = (),
        cwd: Path = None,
        read_condition: Callable[[bytes], bool] = None,
        read_condition_timeout: float = None):
    """Make a method that opens interactive executables."""

    def test(resources: dict):
        try:
            for i in range(count):
                name = f"{executable_name}_i{i}"
                resources[name] = interactive = resources[executable_name].interactive(*args, cwd=cwd)
                if read_condition is not None:
                    interactive.stdout.read(condition=read_condition, timeout=read_condition_timeout)
        except OSError:
            return SetupResult(passing=False, error=Error(description="failed to open process"))
        except TimeoutExpired:
            return SetupResult(passing=False, error=Error(description=f"{executable_name} timed out"))

    return test
