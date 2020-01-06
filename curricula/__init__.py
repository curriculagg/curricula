"""The Curricula package."""

from pathlib import Path

__all__ = ("root",)

root: Path = Path(__file__).absolute().parent
