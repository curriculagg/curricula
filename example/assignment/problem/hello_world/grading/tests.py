from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.check.common import check_file_exists
from curricula.grade.setup.build.common import build_gpp_executable
from curricula.library import files

GPP_OPTIONS = ("-Wall", "-std=c++11")

grader = Grader()


@grader.setup.check(sanity=True)
def check_hello_world(context: Context, resources: dict) -> CheckResult:
    """Check whether hello_world.cpp has been submitted."""

    resources["hello_world_source_path"] = context.problem_directory.joinpath("hello_world.cpp")
    return check_file_exists(resources["hello_world_source_path"])


@grader.setup.build(dependency="check_hello_world", sanity=True)
def build_hello_world(context: Context, hello_world_source_path: Path, resources: dict) -> BuildResult:
    """Compile the program with gcc."""

    resources["hello_world_path"] = context.problem_directory.joinpath("hello_world")
    result, resources["hello_world"] = build_gpp_executable(
        source_path=hello_world_source_path,
        destination_path=resources["hello_world_path"],
        gpp_options=GPP_OPTIONS)
    return result


@grader.test.correctness(dependency="build_hello_world")
def test_hello_world_output(hello_world: ExecutableFile) -> CorrectnessResult:
    """Check if the program outputs as expected."""

    runtime = hello_world.execute(timeout=1)
    return CorrectnessResult(passing=runtime.stdout.strip() == b"Hello, world!", runtime=runtime.dump())


@grader.teardown.cleanup(dependency="build_hello_world")
def cleanup_hello_world(hello_world_path: Path):
    """Clean up executables."""

    if hello_world_path.is_file():
        files.delete_file(hello_world_path)
