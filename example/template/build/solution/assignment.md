# [[ assignment.title ]] Solution

These solutions are intended for course staff only.
Please do not use or redistribute this document if you are not part of the CSCI 104 course staff.

[%- if assignment | has_readme("solution") %]

[[ assignment | get_readme("solution") ]]

[% endif %]

[% for problem in assignment.problems -%]
[% if problem | has_readme("solution") -%]
[%- include "template:build/solution/problem.md" -%]
[% endif %]
[% endfor -%]
