from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.check.common import check_file_exists
from curricula.grade.setup.build.common import build_gpp_executable
from curricula.grade.test.correctness.common import make_stdout_runtime_test
from curricula.library import files

GPP_OPTIONS = ("-Wall", "-std=c++11")

grader = Grader()


@grader.setup.check(sanity=True)
def check_more_cases(context: Context, resources: dict):
    """Check if the program exists."""

    resources["more_cases_source_path"] = context.problem_directory.joinpath("more_cases.cpp")
    return check_file_exists(resources["more_cases_source_path"])


@grader.setup.build(dependency="check_more_cases", sanity=True)
def build_more_cases(more_cases_source_path: Path, resources: dict):
    """Build the program."""

    resources["more_cases_path"] = Path("/tmp", "more_cases")
    result, resources["more_cases"] = build_gpp_executable(
        source_path=more_cases_source_path,
        destination_path=resources["more_cases_path"],
        gpp_options=GPP_OPTIONS)
    return result


test_stdout_pass = make_stdout_runtime_test(out_transform=bytes.strip, test_out=b"pass")


@grader.test.correctness(dependency="build_more_cases", sanity=True)
def test_pass(more_cases: ExecutableFile):
    """Test basic pass."""

    runtime = more_cases.execute("pass")
    return test_stdout_pass(runtime)


@grader.test.correctness(dependency="build_more_cases")
def test_fail(more_cases: ExecutableFile):
    """Test basic fail."""

    runtime = more_cases.execute("fail")
    return test_stdout_pass(runtime)


@grader.test.correctness(dependency="build_more_cases")
def test_fault(more_cases: ExecutableFile):
    """Test basic fail."""

    runtime = more_cases.execute("fault")
    return test_stdout_pass(runtime)


@grader.test.correctness(dependency="build_more_cases")
def test_hang(more_cases: ExecutableFile):
    """Test basic fail."""

    runtime = more_cases.execute("hang", timeout=1)
    return test_stdout_pass(runtime)


@grader.teardown.cleanup(dependency="build_more_cases")
def cleanup_more_cases(more_cases_path: Path):
    """Delete the binary."""

    files.delete_file(more_cases_path)
