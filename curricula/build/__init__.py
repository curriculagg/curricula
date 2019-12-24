"""A package that provides tools for building assignments.

Curricula's build system takes an assignment composed of a set of a
set of problems, and separates the contents of each into combined
instructions, resources, grading, and solution artifacts. The
structure of an assignment is as follows:

assignment/
| README.md
| assignment.json

The structure of a problem is somewhat similar:

problem/
| README.md
| problem.json
| assets/
| | ...
| grading/
| | README.md
| | tests.py
| | ...
| resources/
| | ...
| solution/
| | README.md
| | ...

Typically, problems are located in a sub-folder assignment/problem/.
However, the problems are linked to assignments in the assignment.json
file via relative path, so the problem directory could be anywhere.
"""
