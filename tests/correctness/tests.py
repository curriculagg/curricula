from os.path import dirname, abspath, join
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade import Manager
from grade.resource import Executable, Logger
from grade.correctness import Correctness


test = Manager()
root = dirname(abspath(__file__))
program = Executable(join(root, "program"))


@test.correctness()
def test_pass(target: Executable = program):
    """Basic pass."""

    runtime = target.run("pass", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    return Correctness(passing, runtime)


@test.correctness()
def test_fail(log: Logger, target: Executable = program):
    """Basic pass with fail."""

    runtime = target.run("fail", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    result = Correctness(passing, runtime)
    if not passing:
        log[2]("expected pass, got", runtime.stdout.strip())
    return result


@test.correctness()
def test_error(out: Logger, target: Executable = program):
    """Basic pass with error handling."""

    runtime = target.run("error", timeout=1.0)
    if runtime.code != 0:
        out[2]("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            out[4](line)
        return Correctness(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    out[2]("expected pass, got fail")
    return Correctness(passing, runtime)


@test.correctness()
def test_fault(out: Logger, target: Executable = program):
    """Basic pass with fault detection."""

    runtime = target.run("fault", timeout=1.0)
    if runtime.code != 0:
        out[2]("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            out[2](line)
        if runtime.code == -11:
            out[4]("segmentation fault")
        return Correctness(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    out("expected pass, got fail")
    return Correctness(passing, runtime)


@test.correctness()
def test_timeout(out: Logger, target: Executable = program):
    """Basic pass with timeout."""

    runtime = target.run("hang", timeout=1.0)

    if runtime.timeout:
        return Correctness(False, runtime)

    if runtime.code != 0:
        out("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            out[2](line)
        if runtime.code == -11:
            out[2]("segmentation fault")
        return Correctness(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    out("expected pass, got fail")
    return Correctness(passing, runtime)


if __name__ == "__main__":
    from grade.shell import main
    main(test)
