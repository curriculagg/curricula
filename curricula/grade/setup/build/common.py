from curricula.grade.library import process
from curricula.grade.resource import Logger, Executable
from . import BuildResult

from typing import Iterable, Optional
from pathlib import Path

__all__ = ("build_gpp_executable", "build_makefile_executable")


def build_gpp_executable(
        source: Path,
        destination: Path,
        gpp_options: Iterable[str],
        log: Logger = None,
        timeout: int = 5) -> (BuildResult, Optional[Executable]):
    """Build a binary from a single C++ file with G++."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    runtime = process.run("g++", *gpp_options, "-o", str(destination), str(source), timeout=timeout)
    if runtime.code != 0 or runtime.timeout is not None:
        log and log[2](f"Failed to compile {source.parts[-1]}")
        return BuildResult(passed=False, runtime=runtime.dump(), error="compilation failed"), None
    elif not destination.exists():
        log and log[2](f"Build did not produce {destination.parts[-1]}")
        return BuildResult(passed=False, runtime=runtime.dump(), error="executable not found"), None

    return BuildResult(passed=True, runtime=runtime.dump()), Executable(str(destination))


def build_makefile_executable(
        project_path: Path,
        make_options: Iterable[str] = (),
        log: Logger = None,
        timeout: int = 30) -> BuildResult:
    """Run make on the parent directory."""

    runtime = process.run("make", "-B", "-C", str(project_path), *make_options, timeout=timeout)
    if runtime.code != 0 or runtime.timeout is not None:
        log and log[2](f"Failed to compile {project_path.parts[-1]}")
        return BuildResult(passed=False, runtime=runtime.dump(), error="compilation failed")
    return BuildResult(passed=True, runtime=runtime.dump())
