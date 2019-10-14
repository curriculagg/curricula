# [[ schema.title ]]

This assignment is broken down into 70% for autograding, 15% for good design, and 15% for standard code review.
Note that although there are 33 test cases, that score still counts for 70% of the total assignment score.

[% for problem_short, problem in schema.problems.items() -%]
## [[ problem.title ]] ([[ problem.percentage * 100 ]]%)

Tests score (70%): [[ summary.problems[problem_short].problems_correct ]]/[[ summary.problems[problem_short].problems_total ]]

[% for problem_missed in summary.problems[problem_short].problems_incorrect -%]
- -1 for [[ problem_missed ]]
[% endfor %]
[% endfor -%]

Design score (15%): TOTAL/15

- -POINTS for DEDUCTION
 
Code Review (15%): TOTAL/15

- -POINTS for DEDUCTION
 
