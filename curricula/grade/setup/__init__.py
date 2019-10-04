import abc

from ..task import Result


class SetupResult(Result, abc.ABC):
    """The result of a setup step."""
