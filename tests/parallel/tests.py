from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade.test import Target, Result, register
from grade.test.middleware import iterated


def i(size: int):
    return " " * (size - 1)


@register(name="Parallel 3")
@register(name="Parallel 2")
@register(name="Parallel 1")
@iterated(with_context=False)
def test(target: Target):
    runtime = target.run("2", timeout=3.0)
    yield Result(runtime, runtime.code == 0)


if __name__ == "__main__":
    from grade.standalone import main
    main()
