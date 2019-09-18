from os.path import dirname, abspath, join
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade import Manager
from grade.resource import Executable, Logger
from grade.test.correctness import CorrectnessResult

tests = Manager()
root = dirname(abspath(__file__))
program = Executable(join(root, "program"))


@tests.correctness(name="Parallel 3")
@tests.correctness(name="Parallel 2")
@tests.correctness(name="Parallel 1")
def test(log: Logger, target: Executable = program):
    """Run the test with a program that sleeps."""

    runtime = target.execute("2", timeout=3.0)
    log("written after finish")
    return CorrectnessResult(runtime.code == 0, runtime)


if __name__ == "__main__":
    from grade.shell import main
    main(tests)
