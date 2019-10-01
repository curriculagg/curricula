import sys
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).absolute().parent.parent.parent))
from curricula.grade.shortcuts import *
from curricula.grade.library import valgrind, process

grader = Grader()
root = Path(__file__).absolute().parent


def overwrite_directory(path: Path):
    if path.exists():
        shutil.rmtree(str(path))
    path.mkdir()


@grader.setup(required=True)
def check_program(context: Context, log: Logger):
    """Check if the program has been submitted."""

    if not context.target.joinpath("program.cpp").exists():
        return CheckResult(False, error="missing file test.cpp")
    log[2]("Found program.cpp")
    return CheckResult(True)


@grader.setup(required=True)
def build_program(context: Context, log: Logger, resources: dict):
    """Compile program with GCC."""

    source = context.target.joinpath("program.cpp")
    build = root.joinpath("build")
    overwrite_directory(build)
    executable = build.joinpath("program")

    runtime = process.run("g++", "-Wall", "-o", str(executable), str(source), timeout=5)
    if runtime.code != 0:
        return BuildResult(False, error="failed to build program")

    log[2]("Successfully built program")
    resources["program"] = Executable(str(executable))
    return BuildResult(True)


@grader.test()
def test_memory(program: Executable):
    """Check memory leakage."""

    return MemoryResult.from_valgrind_report(valgrind.run(program.args[0], timeout=2))


if __name__ == "__main__":
    from curricula.grade import main
    main(grader)
