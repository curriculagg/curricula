from os.path import dirname, abspath
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade import Manager, Executable, Messenger
from grade.correctness import Correctness

test = Manager()


@test.correctness(target="program")
def test_pass(executable: Executable, message: Messenger):
    """Basic pass."""

    runtime = executable.run("pass", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    return Correctness(passing, runtime)


@test.correctness(target="program")
def test_fail(target: Executable, message: Messenger):
    """Basic pass with fail."""

    runtime = target.run("fail", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    result = Correctness(passing, runtime)
    if not passing:
        message[2]("Expected pass, got", runtime.stdout.strip())
    return result


@test.correctness(target="program")
def test_error(target: Executable, message: Messenger):
    """Basic pass with error handling."""

    runtime = target.run("error", timeout=1.0)
    if runtime.code != 0:
        message[2]("Received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            message[2](line)
        return Correctness(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    message[2]("Expected pass, got fail")
    return Correctness(passing, runtime)


@test.correctness(target="program")
def test_fault(target: Executable, message: Messenger):
    """Basic pass with fault detection."""

    runtime = target.run("fault", timeout=1.0)
    if runtime.code != 0:
        message[2]("Received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            message[2](line)
        if runtime.code == -11:
            message[2]("Segmentation fault")
        return Correctness(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    message("Expected pass, got fail")
    return Correctness(passing, runtime)


@test.correctness(target="program")
def test_timeout(target: Executable, message: Messenger):
    """Basic pass with timeout."""

    runtime = target.run("hang", timeout=1.0)

    if runtime.timeout:
        return Correctness(False, runtime)

    if runtime.code != 0:
        message("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            message[2](line)
        if runtime.code == -11:
            message[2]("segmentation fault")
        return Correctness(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    message("expected pass, got fail")
    return Correctness(passing, runtime)


if __name__ == "__main__":
    from grade.shell import main
    main(test)
