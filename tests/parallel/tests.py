from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade.test import Manager, Target, Result, Messenger

tests = Manager()


@tests.register(name="Parallel 3")
@tests.register(name="Parallel 2")
@tests.register(name="Parallel 1")
def test(target: Target, message: Messenger):
    runtime = target.run("2", timeout=3.0)
    message("  Written after finish")
    return Result(runtime, runtime.code == 0)


if __name__ == "__main__":
    from grade.shell import main
    main(tests)
