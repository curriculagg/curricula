import os
import shutil
import distutils.dir_util
from pathlib import Path


def overwrite_directory(path: Path):
    """Make sure a directory is present and empty."""

    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def copy(source: Path, destination: Path):
    """Copy a file."""

    if source.is_file():
        copy_file(source, destination)
    else:
        copy_tree(source, destination)


def copy_file(source: Path, destination: Path):
    """Copy a file."""

    shutil.copy(str(source), str(destination))


def copy_tree(source: Path, destination: Path):
    """Copy all files recursively."""

    shutil.copytree(str(source), str(destination))


def delete_file(source: Path):
    """Delete a file."""

    os.remove(str(source))


def copy_tree_overwrite(source: Path, destination: Path):
    """Overwrite while copying recursively."""

    distutils.dir_util.copy_tree(str(source), str(destination))
