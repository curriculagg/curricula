# [[ assignment.title ]] Rubric

[%- if assignment | has_readme("grading") %]

[[ assignment | get_readme("grading") ]]

[% endif %]

[% for problem in assignment.problems -%]
[% if problem | has_readme("grading") -%]
[%- include "template:compile/grading/problem.md" -%]
[% endif %]
[%- endfor %]
