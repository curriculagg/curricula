from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade.test import Manager, Runner, Target, Result, Messenger, pipeline

register, run = pipeline(Manager, Runner)


def i(size: int):
    return " " * (size - 1)


@register(name="Parallel 3")
@register(name="Parallel 2")
@register(name="Parallel 1")
def test(target: Target, message: Messenger):
    runtime = target.run("2", timeout=3.0)
    message("Written after finish")
    return Result(runtime, runtime.code == 0)


if __name__ == "__main__":
    from grade.shell import main
    main(run)
