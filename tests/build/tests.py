from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade import Manager
from grade.resource import Executable, Logger
from grade.test.correctness import CorrectnessResult


test = Manager()
root = dirname(abspath(__file__))


@test.correctness()
def test_pass(target: Executable = program):
    """Basic pass."""

    runtime = target.execute("pass", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    return CorrectnessResult(passing, runtime)


@test.correctness()
def test_fail(log: Logger, target: Executable = program):
    """Basic pass with fail."""

    runtime = target.execute("fail", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    result = CorrectnessResult(passing, runtime)
    if not passing:
        log[2]("expected pass, got", runtime.stdout.strip())
    return result

