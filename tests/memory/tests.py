import sys
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).absolute().parent.parent.parent))
from grade.shortcuts import *
from grade.library import process

grader = Grader()
root = Path(__file__)


@grader.test()
def test_memory():
    """"""

#
# test = Manager()
# root = dirname(abspath(__file__))
# program = Executable(join(root, "program"))

report = valgrind.run("./program", timeout=1.0)
print(report.memory_lost())

# if __name__ == "__main__":
    # from grade.shell import main
    # main(test)
