from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.build.common import build_gpp_executable
from curricula.library import files

GPP_OPTIONS = ("-Wall", "-std=c++11")

grade = Grader()


@grade.setup(required=True)
def check_hello_world(context: Context, resources: dict) -> CheckResult:
    """Check whether hello_world.cpp has been submitted."""

    source_path = context.target_path.joinpath("hello_world", "hello_world.cpp")
    if not source_path.exists():
        return CheckResult(passed=False, error="missing hello_world.cpp")
    resources["hello_world_source_path"] = source_path
    return CheckResult(passed=True)


@grade.setup(required=True)
def build_hello_world(hello_world_source_path: Path, resources: dict) -> BuildResult:
    """Compile the program with gcc."""

    executable_path = Path("/tmp", "hello_world", "hello_world")
    files.replace_directory(executable_path.parent)
    result, executable = build_gpp_executable(hello_world_source_path, executable_path, GPP_OPTIONS)
    resources["hello_world"] = executable
    return result


@grade.test()
def test_output(hello_world: Executable) -> CorrectnessResult:
    """Check if the program outputs as expected."""

    runtime = hello_world.execute(timeout=1)
    return CorrectnessResult(passed=runtime.stdout.strip() == b"Hello, world!", runtime=runtime)


@grade.teardown()
def cleanup(executable_path: Path):
    """Clean up executables."""

    if executable_path.is_file():
        files.delete_file(executable_path)
