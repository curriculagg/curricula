from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(abspath(__file__))))
from grade.test import Target, Result, register
from grade.test.middleware import iterated


@register(middleware=iterated)
def test_pass(target: Target):
    """Basic pass."""

    runtime = target.run("pass")
    passing = runtime.stdout.strip() == "pass"
    yield Result(runtime, passing)
    print("  yeet")


if __name__ == "__main__":
    from grade.standalone import main
    main()
