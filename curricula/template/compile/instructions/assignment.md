# [[ assignment.title ]]

[[ assignment | get_readme ]]

[% for problem in assignment.problems -%]
[% include "template:compile/instructions/problem.md" %]
[%- endfor -%]
