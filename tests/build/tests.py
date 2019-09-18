import sys
from pathlib import Path

sys.path.append(Path(__file__).absolute().parent.parent.parent)
from grade import Grader
from grade.resource import *
from grade.test.correctness import CorrectnessResult
from grade.library.process import run


grader = Grader()
root = Path(__file__).absolute().parent


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

