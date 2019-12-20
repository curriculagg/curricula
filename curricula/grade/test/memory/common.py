from ...library import valgrind
from . import MemoryResult


def make_make_test_memory(executable_name: str):
    """Make a memory test factory from the resource name."""

    def make_test_memory(*args: str, timeout: float = 1):
        """Make the actual memory test."""

        def test_memory(resources: dict):
            executable = resources[executable_name]
            return MemoryResult.from_valgrind_report(valgrind.run(*executable.args, *args, timeout=timeout))

        return test_memory
    return make_test_memory