import os
import tempfile

from typing import Optional

from . import process


def run(*args: str, timeout: float) -> Optional[dict]:
    """Run callgrind on the program and return IR count."""

    path = tempfile.mktemp()
    process.run("valgrind", "--tool=memcheck", "--leak-check=yes", f"--log-file=\"{path}\"", *args, timeout=timeout)
    if os.path.exists(path):
        with open(path) as file:
            print(file.read())
        os.remove(path)
        return None
    return None
