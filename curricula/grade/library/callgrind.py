import os
import tempfile

from typing import Optional

from . import process


def read_last_line(path: str) -> str:
    """IR count appears at the end of the callgrind output."""

    with open(path, "rb") as file:
        file.seek(-2, os.SEEK_END)
        while file.read(1) != b"\n":
            file.seek(-2, os.SEEK_CUR)
        return file.readline().decode()


def run(*args: str, timeout: float) -> Optional[int]:
    """Run callgrind on the program and return IR count."""

    path = tempfile.mktemp()
    process.run("valgrind", "--tool=callgrind", f"--callgrind-out-file=\"{path}\"", *args, timeout=timeout)
    if os.path.exists(path):
        result = int(read_last_line(path).rsplit(maxsplit=1)[1])
        os.remove(path)
        return result
    return None
