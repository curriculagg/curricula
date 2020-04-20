# [[ assignment.title ]] Solution

[%- if assignment | has_readme("solution") %]

[[ assignment | get_readme("solution") ]]

[% endif %]

[% for problem in assignment.problems -%]
[% if problem | has_readme("solution") -%]
[%- include "template:build/solution/problem.md" -%]
[% endif %]
[% endfor -%]
