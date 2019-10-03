import unittest
from pathlib import Path

from curricula.build import build


class BuildBasicTests(unittest.TestCase):
    """Run build but don't really be too picky about result."""

    @classmethod
    def setUpClass(cls):
        """Find the material path."""

        cls.material_path = Path(__file__).absolute().parent.joinpath("material")

    def test_build(self):
        """Build hw1 in the test material."""

        build.build(self.material_path)

    def test_build_assignment(self):
        """Build a specific assignment."""

        build.build(self.material_path, assignment="hw1")
