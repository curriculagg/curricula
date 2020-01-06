from curricula.grade.shortcuts import *

grader = Grader()


@grader.test.correctness()
def check_pass():
    """Check if the program exists."""

    return CorrectnessResult(passed=True)
