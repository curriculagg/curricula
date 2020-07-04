[%- set problem_summary = summary.problems[problem.short] %]

## [[ problem.title ]] ([[ problem.grading.percentage() | percentage ]])

[%- if problem.grading.is_automated %]

Tests score: [[ problem_summary.tests_fraction ]] ([[ problem_summary.tests_percentage | percentage ]])
[%- if problem_summary.setup_results_errored %]

The followed tasks failed:

[% for result in problem_summary.setup_results_errored -%]
- Task [[ result.task.name ]] failed: [[ result.error.description ]]
[%- if result.error.traceback %]
  
    ```
    [[ result.error.traceback | indent | trim ]]
    ```
[%- endif %]
[% endfor %]
[% endif %]

[%- if problem_summary.test_results_failing %]

The following tests did not pass:

[%- for result in problem_summary.test_results_failing %]
- -[[ result.task.details.get("weight", 1) ]] for [[ result.task.name ]]
[%- endfor -%]
[%- endif -%]
[%- endif -%]

[%- if problem.grading.is_review %]

Review score: ?/[[ problem.grading.points_review | pretty ]]
[%- endif -%]

[%- if problem.grading.is_manual %]

Manual score: ?/[[ problem.grading.points_manual | pretty ]]
[%- endif -%]
