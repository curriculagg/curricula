import sys
from pathlib import Path

# Add the repository directory to path so we can import from our local copy of curricula
# We can also use these path objects when we need to access files from around us
root = Path(__file__).absolute().parent  # /
repository = root.parent.parent          # /tests/runtime/

sys.path.append(str(repository))

# Import stuff from curricula here, some useful examples are included
from curricula.grade.setup.build.common import build_gpp_executable
from curricula.grade.library import callgrind
from curricula.library.files import delete_file
from curricula.library.utility import timed


def example():
    """An example of how to use some of the provided tools."""

    # Make sure a build directory exists
    root.joinpath("build").mkdir(exist_ok=True)

    # Here's a convenient way to build a file with G++
    result, executable = build_gpp_executable(
        root.joinpath("tests", "example.cpp"),
        root.joinpath("build", "example"),
        gpp_options=("-Wall", "-std=c++11"),
        timeout=30)

    if not result.passed:
        stderr = result.details["runtime"]["stderr"]
        print(f"Whoops, couldn't compile:\n{stderr}")
        return

    # Run the executable
    runtime = executable.execute("1", "2", "3", timeout=1)
    print(runtime.stdout)

    # This timer is approximately accurate, but is not super precise and is not tied to CPU so can vary with load
    print(f"Ran in {runtime.elapsed} seconds")

    # Count instructions
    instruction_count = executable.count("1", "2", "3", timeout=10)
    print(f"Ran in {instruction_count} instructions")


if __name__ == "__main__":
    example()
