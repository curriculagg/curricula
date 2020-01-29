from curricula.grade.shortcuts import *

grader = Grader()
grader.output.add_required_task_detail("weight", 1)


@grader.test.correctness(weight=10)
def check_heavy_pass():
    """Check if the program exists."""

    return CorrectnessResult(passed=True)


@grader.test.correctness(weight=10)
def check_heavy_fail():
    """Check if the program exists."""

    return CorrectnessResult(passed=False)


@grader.test.correctness(weight=1)
def check_normal_pass():
    """Check if the program exists."""

    return CorrectnessResult(passed=True)


@grader.test.correctness(weight=1)
def check_normal_fail():
    """Check if the program exists."""

    return CorrectnessResult(passed=False)


@grader.test.correctness(weight=0.1)
def check_light_pass():
    """Check if the program exists."""

    return CorrectnessResult(passed=True)


@grader.test.correctness(weight=0.1)
def check_light_fail():
    """Check if the program exists."""

    return CorrectnessResult(passed=False)
