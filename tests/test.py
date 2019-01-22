from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(abspath(__file__))))
from grade.test import Target, Result, register


@register(name="pass")
def test_pass(target: Target):
    runtime = target.run("pass")
    passing = runtime.stdout.strip() == "pass"
    return Result(runtime, passing)


if __name__ == "__main__":
    from grade.standalone import main
    main()
