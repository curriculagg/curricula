from os.path import dirname, abspath, join
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade import Manager
from grade.resource import Executable, Logger
from grade.complexity import ComplexityResult


test = Manager()
root = dirname(abspath(__file__))
program = Executable(join(root, "program"))


@test.complexity()
def test_pass(log: Logger, target: Executable = program):
    """Basic pass."""

    runtimes = []
    for i in range(10):
        runtimes.append(target.count("linear", str(i*100), timeout=1))
    log(runtimes)
    return ComplexityResult(True)


if __name__ == "__main__":
    from grade.shell import main
    main(test)