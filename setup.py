import importlib.util
from setuptools import setup, find_packages
from pathlib import Path


root = Path(__file__).absolute().parent

with root.joinpath("README.md").open() as fh:
    long_description = fh.read()

version = importlib.util.spec_from_file_location("version", str(root.joinpath("curricula", "version.py")))
module = importlib.util.module_from_spec(version)
version.loader.exec_module(module)


setup(
    name="curricula",
    version=module.version,
    description="A content manager and grading toolkit for evaluating student code",
    url="https://github.com/curriculagg/curricula",
    author="Noah Kim",
    author_email="noahbkim@gmail.com",

    # Extra
    long_description=long_description,
    long_description_content_type="text/markdown",

    # Python
    python_requires=">=3.9",

    # Packaging
    packages=find_packages(),
    zip_safe=False)
