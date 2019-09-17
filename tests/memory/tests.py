from os.path import dirname, abspath, join
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade import Manager
from grade.resource import Executable, Logger
from grade.library import valgrind
from grade.correctness import CorrectnessResult

#
# test = Manager()
# root = dirname(abspath(__file__))
# program = Executable(join(root, "program"))

report = valgrind.run("./program", timeout=1.0)
print(report.memory_lost())

# if __name__ == "__main__":
    # from grade.shell import main
    # main(test)
