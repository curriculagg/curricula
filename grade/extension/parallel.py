import multiprocessing
from typing import Dict

from grade.runner import Runner
from grade.test import Test
from grade.resource import Executable, Logger
from grade.library.utility import timed


def worker(test: Test, resources: dict, output: multiprocessing.Queue):
    log = Logger()
    result = test.run(**resources)
    log.sneak("{} {}".format(test, result))
    output.put(log.build(prefix=" " * 2))
    return test, result


class ParallelRunner(Runner):
    """A parallel processing runner."""

    _pool: multiprocessing.Pool
    _manager: multiprocessing.Manager
    _output: multiprocessing.Queue
    _leave_open: bool

    def __init__(self):
        super().__init__()
        self._pool = None
        self._manager = multiprocessing.Manager()
        self._output = self._manager.Queue()
        self._leave_open = False

    def _open_pool(self, *, workers: int):
        if self._pool is None:
            self._pool = multiprocessing.Pool(processes=workers)

    def _close_pool(self):  # Pool's closed
        if self._pool is not None and not self._leave_open:
            self._pool.join()

    @timed(name="Parallel tests")
    def run(self, workers: int = None, **resources) -> Dict[Executable, ]:
        """Run all tests on the target in multiple processes."""

        print("Starting tests in parallel...")
        workers = min(workers or multiprocessing.cpu_count(), len(self.tests))
        self._open_pool(workers=workers)
        values = self._pool.starmap(worker, ((test, resources, self._output) for test in self.tests))

        for i in range(len(self.tests)):
            print(self._output.get())

        results = {}
        for test, result in values:
            results[test] = result

        return results
