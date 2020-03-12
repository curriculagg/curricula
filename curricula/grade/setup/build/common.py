import stat
from typing import Iterable, Optional, Tuple
from pathlib import Path

from . import BuildResult
from ...resource import ExecutableFile, File
from ....library import process
from ....library.files import delete_file, add_mode

__all__ = ("build_gpp_executable", "build_makefile_executable", "build_harness_library")


def build_gpp_executable(
        source_path: Path,
        *source_paths: Path,
        destination_path: Path,
        gpp_options: Iterable[str] = (),
        timeout: float = None) -> Tuple[BuildResult, Optional[ExecutableFile]]:
    """Build a binary from a single C++ file with G++."""

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    runtime = process.run(
        "g++", *gpp_options,
        "-o", str(destination_path),
        str(source_path),
        *map(str, source_paths),
        timeout=timeout)

    error = None
    if runtime.raised_exception:
        error = f"error invoking compilation of {source_path.parts[-1]}: {runtime.exception.description}"
    elif runtime.timed_out:
        error = f"timed out while compiling {source_path.parts[-1]}"
    elif runtime.code != 0:
        if runtime.stderr:
            error = runtime.stderr.decode(errors="replace")
        else:
            error = "nonzero status code"
    elif not destination_path.exists():
        error = f"build did not produce {destination_path.parts[-1]}"

    # If the build failed
    if error is not None:
        return BuildResult(passed=False, runtime=runtime.dump(), error=error), None

    # Chmod
    add_mode(destination_path, stat.S_IXOTH)

    # Otherwise
    return BuildResult(passed=True, runtime=runtime.dump()), ExecutableFile(destination_path)


def build_makefile_executable(
        target_path: Path,
        make_options: Iterable[str] = (),
        timeout: float = None) -> BuildResult:
    """Run make on the target directory."""

    runtime = process.run("make", "-B", "-C", str(target_path), *make_options, timeout=timeout)
    if runtime.code != 0 or runtime.timed_out:
        error = f"failed to make {target_path.parts[-1]}"
        return BuildResult(passed=False, runtime=runtime.dump(), error=error)
    return BuildResult(passed=True, runtime=runtime.dump())


def build_harness_library(
        harness_path: Path,
        include_paths: Iterable[Path] = (),
        object_paths: Iterable[Path] = (),
        gpp_options: Iterable[str] = (),
        build_path: Path = Path(),
        timeout: int = 30) -> (BuildResult, Optional[File]):
    """Build a shared object file.

    The target path will be listed after an include flag so that
    headers may be imported.
    """

    object_path = build_path.joinpath("harness.o")
    runtime = process.run(
        "g++", "-Wall", "-c", "-fPIC", *gpp_options,
        str(harness_path.absolute()),
        *map(lambda path: f"{path.absolute()}", object_paths),
        *map(lambda path: f"-I{path.absolute()}", include_paths),
        "-o", str(object_path),
        timeout=timeout)
    if runtime.code != 0 or runtime.raised_exception is not None:
        return BuildResult(passed=False, runtime=runtime.dump(), error="compilation failed"), None

    shared_object_path = build_path.joinpath("harness.so")
    runtime = process.run("g++", "-shared", str(object_path), "-o", str(shared_object_path), timeout=timeout)
    delete_file(object_path)
    if runtime.code != 0 or runtime.raised_exception is not None:
        return BuildResult(passed=False, runtime=runtime.dump(), error="shared library build failed"), None

    return BuildResult(passed=True), File(shared_object_path)
