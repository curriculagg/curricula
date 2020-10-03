import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from . import process
from .files import delete_file

__all__ = ("count",)


def read_last_line(path: Path) -> Optional[str]:
    """IR count appears at the end of the callgrind output."""

    with path.open("rb") as file:
        if len(file.read(2)) < 2:
            return None

        file.seek(0)
        file.seek(-2, os.SEEK_END)
        while file.read(1) != b"\n":
            file.seek(-2, os.SEEK_CUR)
            if file.tell() == 0:
                return None
        return file.readlines()[-1].decode()


def count(
        *args: str,
        stdin: bytes = None,
        timeout: float = None,
        cwd: Path = None,
        function_name: str = None) -> Tuple[process.Runtime, Optional[int]]:
    """Run callgrind on the program and return IR count."""

    extra_valgrind_args = []
    if function_name is not None:
        extra_valgrind_args.append(f"--toggle-collect={function_name}")

    out_path = Path(next(tempfile._get_candidate_names()))
    runtime = process.run(
        "valgrind",
        "--tool=callgrind",
        f"--callgrind-out-file={out_path.parts[-1]}",
        *extra_valgrind_args,
        *args,
        stdin=stdin,
        timeout=timeout,
        cwd=cwd)
    if out_path.exists():
        last_line = read_last_line(out_path)
        if last_line is None:
            return runtime, None
        result = int(last_line.rsplit(maxsplit=1)[1])
        delete_file(out_path)
        return runtime, result
    return runtime, None
