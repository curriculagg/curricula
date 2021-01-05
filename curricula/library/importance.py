import importlib.util
from importlib import import_module

from pathlib import Path
from typing import Any

__all__ = (
    "import_module",
    "import_file_at_path",
    "import_module_at_path",
    "import_file_or_module_at_path")


def import_file_at_path(path: Path, module_name: str = None) -> Any:
    """Assumes the path is a file that exists."""

    if module_name is None:
        module_name = path.parts[-1].split(".", maxsplit=1)[0]

    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_module_at_path(path: Path, module_name: str = None) -> Any:
    """Assumes that __init__.py exists in the directory."""

    if module_name is None:
        module_name = path.parts[-1]

    spec = importlib.util.spec_from_file_location(module_name, str(path.joinpath("__init__.py")))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_file_or_module_at_path(path: Path, module_name: str = None) -> Any:
    """Import an object from a path."""

    if path.joinpath("__init__.py").is_file():
        return import_module_at_path(path, module_name=module_name)
    return import_file_at_path(Path(*path.parts[:-1], path.parts[-1] + ".py"), module_name=module_name)
