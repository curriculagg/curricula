from typing import Callable


class Result:
    """The result of a test."""

    passing: bool

    def __init__(self, passing: bool):
        self.passing = passing

    def __str__(self):
        return "passed" if self.passing else "failed"

    def __repr__(self):
        return "Result[{}]".format(str(self))


Runnable = Callable[[...], Result]


class Test:
    """A general test for a codebase.

    From this class the correctness, complexity, and style tests are
    derived such that they can be run generically. It is intended to
    wrap a raw runnable with metadata used during registration.
    """

    name: str
    runnable: Callable[[...], Result]
    details: dict

    def __init__(self, name: str, runnable: Runnable, **details):
        self.name = name
        self.runnable = runnable
        self.details = details

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Test[{}]".format(str(self))

    def run(self, *args, **kwargs) -> Result:
        return self.runnable(*args, **kwargs)
