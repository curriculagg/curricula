from typing import Callable
from functools import wraps

from ..test import Testable, Target, Test, Result


def iterated(with_context: bool = True) -> Callable[[Callable], Testable]:
    """Nicely format a test case."""

    def wrapper(test: Callable) -> Testable:

        @wraps(test)
        def wrapped(context: Test, target: Target) -> Result:
            print(context.name, end=" ")
            generator = test(context, target) if with_context else test(target)
            result = next(generator)
            print(result, "***" if not result.passing else "")
            next(generator, None)
            return result
        return wrapped

    return wrapper
