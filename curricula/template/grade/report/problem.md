[%- set problem_summary = summary.problems[problem.short] %]

## [[ problem.title ]] ([[ problem.grading.percentage() | percentage ]])

Total score: ?/[[ problem.grading.points ]]

[%- if problem.grading.is_automated %]

Tests score ([[ problem.grading.percentage_automated | percentage ]]): [[ problem_summary.passing_fraction ]] tests, **[[ problem_summary.points_fraction ]] points ([[ problem_summary.points_percentage | percentage ]])**
[%- if problem_summary.setup_results_errored %]

The followed tasks failed:

[% for result in problem_summary.setup_results_errored -%]
- Task [[ result.task.name ]] failed: [[ result.error.description ]]
[%- if result.error.traceback %]
  
    ```
    [[ result.error.traceback | indent | trim ]]
    ```
[%- endif %]
[%- endfor %]
[%- endif %]

[%- if problem_summary.test_results_passing_count < problem_summary.test_results_count %]

The following tests did not pass:

[%- for result in problem_summary.test_results_failing %]
- -[[ (result.task.weight * problem.grading.automated_point_ratio) | pretty ]] for test `[[ result.task.name ]]`
[%- endfor -%]
[%- endif -%]
[%- endif -%]

[%- if problem.grading.is_review %]

Review score ([[ problem.grading.percentage_review | percentage ]]): **?/[[ problem.grading.review.points | pretty ]] points**
[%- endif -%]

[%- if problem.grading.is_manual %]

Manual score ([[ problem.grading.percentage_manual | percentage ]]): **?/[[ problem.grading.manual.points | pretty ]] points**
[%- endif -%]
