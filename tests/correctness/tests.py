from pathlib import Path
import sys

sys.path.append(str(Path(__file__).absolute().parent.parent.parent))
from grade import Grader
from grade.resource import *
from grade.test.correctness import CorrectnessResult
from grade.library.process import run


grader = Grader()
root = Path(__file__).absolute().parent


@grader.build(name="program")
def build_program(context: Context):
    """Compile program with GCC."""

    source = context.target.joinpath("program.cpp")
    build = root.joinpath("build")
    build.mkdir()
    executable = build.joinpath("program")
    runtime = run("g++", "-Wall", "-o", str(executable), str(source), timeout=1)
    if runtime.code == 0:
        return Executable(str(executable))
    raise Exception()


@grader.test()
def test_pass(program: Executable):
    """Basic pass."""

    runtime = program.execute("pass", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    return CorrectnessResult(passing, runtime)


@grader.test()
def test_fail(log: Logger, program: Executable):
    """Basic pass with fail."""

    runtime = program.execute("fail", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    result = CorrectnessResult(passing, runtime)
    if not passing:
        log[2]("expected pass, got", runtime.stdout.strip())
    return result


@grader.test()
def test_error(out: Logger, program: Executable):
    """Basic pass with error handling."""

    runtime = program.execute("error", timeout=1.0)
    if runtime.code != 0:
        out[2]("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            out[4](line)
        return CorrectnessResult(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    out[2]("expected pass, got fail")
    return CorrectnessResult(passing, runtime)


@grader.test()
def test_fault(out: Logger, program: Executable):
    """Basic pass with fault detection."""

    runtime = program.execute("fault", timeout=1.0)
    if runtime.code != 0:
        out[2]("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            out[4](line)
        if runtime.code == -11:
            out[4]("segmentation fault")
        return CorrectnessResult(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    out("expected pass, got fail")
    return CorrectnessResult(passing, runtime)


@grader.test()
def test_timeout(out: Logger, program: Executable):
    """Basic pass with timeout."""

    runtime = program.execute("hang", timeout=1.0)

    if runtime.timeout:
        return CorrectnessResult(False, runtime)

    if runtime.code != 0:
        out("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            out[2](line)
        if runtime.code == -11:
            out[2]("segmentation fault")
        return CorrectnessResult(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    out("expected pass, got fail")
    return CorrectnessResult(passing, runtime)


if __name__ == "__main__":
    from grade.shell import main
    main(grader)
