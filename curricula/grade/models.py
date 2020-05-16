from typing import List, Optional

from ..models import Assignment, Problem
from .task import Task
from .grader import Grader


class GradingProblem(Problem):
    """Additional details for grading."""

    tasks: Optional[List[Task]]
    grader: Grader



class GradingAssignment(Assignment):
    """Additional details for grading."""
