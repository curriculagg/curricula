import os
import shutil
import distutils.dir_util
from pathlib import Path


def copy(source: Path, destination: Path):
    """Copy a file."""

    if source.is_file():
        copy_file(source, destination)
    else:
        copy_directory(source, destination)


def copy_file(source: Path, destination: Path):
    """Copy a file."""

    shutil.copy(str(source), str(destination))


def copy_directory(source: Path, destination: Path, merge: bool = True):
    """Copy all files recursively."""

    if merge:
        distutils.dir_util.copy_tree(str(source), str(destination))
    else:
        shutil.copytree(str(source), str(destination))


def delete(source: Path):
    """Delete a file or directory."""

    if source.is_file():
        delete_file(source)


def delete_file(path: Path):
    """Delete a file."""

    os.remove(str(path))


def delete_directory(path: Path):
    """Delete a directory recursively."""

    shutil.rmtree(str(path))


def replace_directory(path: Path):
    """Make sure a directory is present and empty."""

    if path.exists():
        delete(path)
    path.mkdir(parents=True)
