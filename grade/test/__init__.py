from .runtime import Target, Runtime
from .test import Result, Testable, Test, Tests

tests = Tests()
register = tests.register
run = tests.run
