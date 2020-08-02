import os
import shutil
import distutils.dir_util
from pathlib import Path


def contains(parent: Path, child: Path) -> bool:
    """Check if the child path is within the parent path."""

    for a, b in zip(parent.resolve().parts, child.resolve().parts):
        if a is None:
            return True
        if a != b:
            return False
    return True


def relative(root: Path, path: Path):
    """Left-truncate the path by the root."""

    return Path(*path.parts[len(root.parts):])


def move(source: Path, destination: Path):
    """Rename a file."""

    shutil.move(str(source), str(destination))


def copy(source: Path, destination: Path):
    """Copy a file."""

    if source.is_file():
        copy_file(source, destination)
    else:
        copy_directory(source, destination)


def copy_file(source: Path, destination: Path):
    """Copy a file."""

    shutil.copy(str(source), str(destination))


def copy_directory(source: Path, destination: Path, merge: bool = False):
    """Copy all files recursively."""

    if merge:
        distutils.dir_util.copy_tree(str(source), str(destination))
    else:
        if destination.exists():
            delete(destination)
        shutil.copytree(str(source), str(destination))


def delete(path: Path):
    """Delete a file or directory."""

    if path.is_file():
        delete_file(path)
    else:
        delete_directory(path)


def delete_file(path: Path):
    """Delete a file."""

    os.remove(str(path))


def delete_directory(path: Path):
    """Delete a directory recursively."""

    shutil.rmtree(str(path))


def replace_directory(path: Path):
    """Make sure a directory is present and empty."""

    if path.is_file() or path.is_dir():
        delete(path)
    path.mkdir(parents=True)


def add_mode(path: Path, mode: int):
    """Do chmod and add a mode."""

    os.chmod(str(path), os.stat(str(path)).st_mode | mode)


def subtract_mode(path: Path, mode: int):
    """Do chmod and subtract a mode."""

    os.chmod(str(path), os.stat(str(path)).st_mode & ~mode)
