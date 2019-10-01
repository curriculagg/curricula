from typing import Optional
from pathlib import Path

from ..resource import Logger
from . import CheckResult


def check_file_exists(log: Logger, path: Path) -> CheckResult:
    """Check if a file is present in the directory."""

    if not path.exists():
        log[2](f"Can't find {path.parts[-1]}!")
        return CheckResult(passed=False, error=f"can't find {path.parts[-1]}")

    log[2](f"Found {path.parts[-1]}")
    return CheckResult(passed=True)


def search_file_by_name(name: str, path: Path) -> Optional[Path]:
    """Find file by name, None if none or multiple."""

    results = tuple(path.glob(f"**/{name}"))
    if len(results) == 1:
        return results[0]
    return None
