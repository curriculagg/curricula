from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade.test import Target, Result, Manager, Messenger

tests = Manager()


def i(size: int):
    return " " * (size - 1)


@tests.register()
def test_pass(target: Target, message: Messenger):
    """Basic pass."""

    runtime = target.run("pass", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    return Result(runtime, passing)


@tests.register()
def test_fail(target: Target, message: Messenger):
    """Basic pass with fail."""

    runtime = target.run("fail", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    result = Result(runtime, passing)
    if not passing:
        message("  expected pass, got", runtime.stdout.strip())
    return result


@tests.register()
def test_error(target: Target, message: Messenger):
    """Basic pass with error handling."""

    runtime = target.run("error", timeout=1.0)
    if runtime.code != 0:
        message("  received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            message(" ", line)
        return Result(runtime, False)

    passing = runtime.stdout.strip() == "pass"
    message("  expected pass, got fail")
    return Result(runtime, passing)


@tests.register()
def test_fault(target: Target, message: Messenger):
    """Basic pass with fault detection."""

    runtime = target.run("fault", timeout=1.0)
    if runtime.code != 0:
        message("  received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            message(" ", line)
        if runtime.code == -11:
            message("  segmentation fault")
        return Result(runtime, False)

    passing = runtime.stdout.strip() == "pass"
    message("expected pass, got fail")
    return Result(runtime, passing)


@tests.register()
def test_timeout(target: Target, message: Messenger):
    """Basic pass with timeout."""

    runtime = target.run("hang", timeout=1.0)

    if runtime.timeout is not None:
        return Result(runtime, False)

    if runtime.code != 0:
        message("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            message(" ", line)
        if runtime.code == -11:
            message("  segmentation fault")
        return Result(runtime, False)

    passing = runtime.stdout.strip() == "pass"
    message("expected pass, got fail")
    return Result(runtime, passing)


if __name__ == "__main__":
    from grade.shell import main
    main(tests)
