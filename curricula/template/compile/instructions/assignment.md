# [[ assignment.title ]]

[[ assignment | get_readme ]]

[% for problem in assignment.problems -%]
[% if problem | has_readme -%]
[% include "template:compile/instructions/problem.md" %]
[% endif %]
[%- endfor -%]
