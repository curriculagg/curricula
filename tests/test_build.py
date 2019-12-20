import unittest
from pathlib import Path

from curricula.build import build

root = Path(__file__).absolute().parent


class BuildBasicTests(unittest.TestCase):
    """Run build but don't really be too picky about result."""

    def test_build(self):
        """Build hw1 in the test material."""

        build.build(root.joinpath("assignment", "hw1"), root.joinpath("artifacts", "hw1"))
