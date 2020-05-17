[%- set problem_summary = summary.problems[problem.short] %]

## [[ problem.title ]] ([[ problem.grading.weight | percentage ]])

[[ problem_summary ]]

Tests score: [[ problem_summary.tests_fraction ]] ([[ problem_summary.tests_percentage | percentage ]])
[% if problem_summary.setup_failed %]
Setup failed:

```
[[ problem_summary.setup_error | trim ]]
```
[% else %]
[%- for test_missed in problem_summary.tests_incorrect %]
- -[[ test_missed["details"].get("weight", 1) ]] for [[ test_missed.name ]]
[%- endfor -%]
[%- endif -%]
