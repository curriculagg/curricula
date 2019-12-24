from curricula.grade.library import process
from curricula.grade.resource import ExecutableFile, File
from curricula.library.files import delete_file
from . import BuildResult

from typing import Iterable, Optional, Tuple
from pathlib import Path

__all__ = ("build_gpp_executable", "build_makefile_executable", "build_harness_library")


def build_gpp_executable(
        source: Path,
        destination: Path,
        gpp_options: Iterable[str] = (),
        timeout: int = 5) -> Tuple[BuildResult, Optional[ExecutableFile]]:
    """Build a binary from a single C++ file with G++."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    runtime = process.run("g++", *gpp_options, "-o", str(destination), str(source), timeout=timeout)
    if runtime.code != 0 or runtime.timeout is not None:
        error = f"failed to compile {source.parts[-1]}"
        return BuildResult(passed=False, runtime=runtime.dump(), error=error), None
    elif not destination.exists():
        error = f"build did not produce {destination.parts[-1]}"
        return BuildResult(passed=False, runtime=runtime.dump(), error=error), None

    return BuildResult(passed=True, runtime=runtime.dump()), ExecutableFile(destination)


def build_makefile_executable(
        target_path: Path,
        make_options: Iterable[str] = (),
        timeout: int = 30) -> BuildResult:
    """Run make on the target directory."""

    runtime = process.run("make", "-B", "-C", str(target_path), *make_options, timeout=timeout)
    if runtime.code != 0 or runtime.timeout is not None:
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
    if runtime.code != 0 or runtime.error is not None:
        return BuildResult(passed=False, runtime=runtime.dump(), error="compilation failed"), None

    shared_object_path = build_path.joinpath("harness.so")
    runtime = process.run("g++", "-shared", str(object_path), "-o", str(shared_object_path), timeout=timeout)
    delete_file(object_path)
    if runtime.code != 0 or runtime.error is not None:
        return BuildResult(passed=False, runtime=runtime.dump(), error="shared library build failed"), None

    return BuildResult(passed=True), File(shared_object_path)
