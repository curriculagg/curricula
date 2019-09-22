import abc

from ..task import Result


class TestResult(Result, abc.ABC):
    """The result of a test."""
