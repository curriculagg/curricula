from curricula.grade.library import process
from curricula.grade.resource import Logger, Executable
from . import BuildResult

from typing import Iterable, Optional
from pathlib import Path


def build_gpp_executable(
        source: Path,
        destination: Path,
        gpp_options: Iterable[str],
        log: Optional[Logger] = None,
        timeout: int = 5) -> (BuildResult, Optional[Executable]):
    """Build a binary from a single C++ file with G++."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    runtime = process.run("g++", *gpp_options, "-o", str(destination), str(source), timeout=timeout)
    if runtime.code != 0:
        log and log[2](f"Failed to compile {source.parts[-1]}")
        return BuildResult(passed=False, runtime=runtime.dump(), error="compilation failed"), None
    elif not destination.exists():
        log and log[2](f"Build did not produce {destination.parts[-1]}")
        return BuildResult(passed=False, runtime=runtime.dump(), error="executable not found"), None

    return BuildResult(passed=True, runtime=runtime.dump()), Executable(str(destination))
