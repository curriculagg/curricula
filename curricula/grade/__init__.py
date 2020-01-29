"""Grade is a combined library for grading C++ problem sets.

Grade is capable of testing three main aspects of C++ programs:
correctness, efficiency, and style. It includes tools for testing the
output of the code under various conditions, measuring its runtime
performance and memory usage, and running style checks.
"""

from pathlib import Path

ROOT = Path(__file__).absolute().parent
INCLUDE_PATH = ROOT.joinpath("include")
