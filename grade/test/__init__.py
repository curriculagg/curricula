from .runtime import Target, Runtime
from .test import Result, Testable, Test
from .manager import Manager
from .runner import Runner
from .message import Messenger

from typing import Tuple, Callable


def pipeline(manager_type, runner_type) -> Tuple[Callable, Callable]:
    """Build a manager, runner, writer pipeline.

    Returns a test registration function and a run function. Will
    eventually also return an output function.
    """

    manager = manager_type()
    runner = runner_type()

    def run(target: Target):
        runner.load(manager.tests)
        runner.run(target)

    return manager.register, run
