from os.path import dirname, abspath, join
import sys

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from grade import Manager, Executable, Messenger
from grade.correctness import Correctness


test = Manager()

root = dirname(__file__)
Program = Executable(join(root, "program"))


@test.correctness()
def test_pass(program: Program):
    """Basic pass."""

    runtime = program.run("pass", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    return Correctness(passing, runtime)


# @test.correctness()
# def test_fail(target: Executable, out: Messenger):
#     """Basic pass with fail."""
#
#     runtime = target.run("fail", timeout=1)
#     passing = runtime.stdout.strip() == "pass"
#     result = Correctness(passing, runtime)
#     if not passing:
#         out[2]("Expected pass, got", runtime.stdout.strip())
#     return result
#
#
# @test.correctness(target="program")
# def test_error(target: Executable, out: Messenger):
#     """Basic pass with error handling."""
#
#     runtime = target.run("error", timeout=1.0)
#     if runtime.code != 0:
#         out[2]("Received return code", runtime.code)
#         for line in filter(None, runtime.stderr.split("\n")):
#             out[2](line)
#         return Correctness(False, runtime)
#
#     passing = runtime.stdout.strip() == "pass"
#     out[2]("Expected pass, got fail")
#     return Correctness(passing, runtime)
#
#
# @test.correctness(target="program")
# def test_fault(target: Executable, out: Messenger):
#     """Basic pass with fault detection."""
#
#     runtime = target.run("fault", timeout=1.0)
#     if runtime.code != 0:
#         out[2]("Received return code", runtime.code)
#         for line in filter(None, runtime.stderr.split("\n")):
#             out[2](line)
#         if runtime.code == -11:
#             out[2]("Segmentation fault")
#         return Correctness(False, runtime)
#
#     passing = runtime.stdout.strip() == "pass"
#     out("Expected pass, got fail")
#     return Correctness(passing, runtime)
#
#
# @test.correctness(target="program")
# def test_timeout(target: Executable, out: Messenger):
#     """Basic pass with timeout."""
#
#     runtime = target.run("hang", timeout=1.0)
#
#     if runtime.timeout:
#         return Correctness(False, runtime)
#
#     if runtime.code != 0:
#         out("received return code", runtime.code)
#         for line in filter(None, runtime.stderr.split("\n")):
#             out[2](line)
#         if runtime.code == -11:
#             out[2]("segmentation fault")
#         return Correctness(False, runtime)
#
#     passing = runtime.stdout.strip() == "pass"
#     out("expected pass, got fail")
#     return Correctness(passing, runtime)


if __name__ == "__main__":
    from grade.shell import main
    main(test)
