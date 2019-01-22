from typing import Callable, Iterator

from ..test import Testable, Target, Result


IteratorTestable = Callable[[Target], Iterator[Result]]


def iterated(test: IteratorTestable, **details) -> Testable:
    """Nicely format a test case."""

    def decorated(target: Target) -> Result:
        """The actual test to be run."""

        print(details["name"], end=" ")
        generator = test(target)
        result = next(generator)
        print(result, "***" if not result.passing else "")
        next(generator, None)
        return result

    return decorated
