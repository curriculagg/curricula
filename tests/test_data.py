import unittest
from pathlib import Path

from curricula.data.material import Problem, Assignment

root = Path(__file__).absolute().parent


class DataTests(unittest.TestCase):
    """Test container loading."""

    def setUp(self):
        """Check whether a problem is deserialized correctly."""

        self.assignment = Assignment.load(root.joinpath("material", "assignment", "hw1"))

    def test_assignment_instance(self):
        """Confirm that the assignment is what's expected."""

        self.assertIsInstance(self.assignment, Assignment)

    def test_assignment_contents(self):
        """Test whether the assignment loaded correctly."""

        self.assertEqual(self.assignment.title, "Homework 1")
        self.assertEqual(self.assignment.short, "hw1")

    def test_problem_instance(self):
        """Check problems in assignment."""

        self.assertIsInstance(self.assignment.problems[0], Problem)

    def test_problem_contents(self):
        """Check if problem contents matches up."""

        self.assertEqual(self.assignment.problems[0].title, "Hello, World!")
        self.assertEqual(self.assignment.problems[0].short, "hello_world")
        self.assertEqual(self.assignment.problems[0].percentage, 1)
