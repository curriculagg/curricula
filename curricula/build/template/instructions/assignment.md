# [[ assignment.title ]]

[[ assignment | get_readme ]]

[% for problem in assignment.problems -%]
[% include "template:build/instructions/problem.md" %]
[%- endfor -%]
