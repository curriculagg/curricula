This C++ source code rubric is separated into sections delineating penalized submission rules.
Point deductions for each infraction are included, and are to be taken from a starting (and maximum possible) score of 100.

### Submission

Submission rules are likely the first item graded on this rubric.
Note that the `README.md` requirements only apply to homeworks where the file is required.

| Infraction | Points | Notes |
|---|---|---|
| Missing submission | 100 points | |
| Unclear or missing `README.md` | 2 points | |
| Extra files | 1 point per file, max 3 | Ignore test files |
| Incorrect file format | 1 point per file, max 5 | |
| Corrupt or unopenable file | All points for related problems | |

### Makefile

All `Makefile` rules only apply when students are required to provide a build system.
If the program is intended to be compiled by the autograder, they may be disregarded.

| Infraction | Points | Notes |
|---|---|---|
| Missing `Makefile` | 5 points | Spend 10 minutes compiling the code |
| Able to compile | 3 points per related problem | Re-run the autograder with the binary |
| Unable to compile | All points for related problems | Still do code review |

### Compilation

Compilation errors also incur a penalty.
Going forward we will work on automating this portion of grading.

| Infraction | Points | Notes |
|---|---|---|
| Compiler errors | 3 points per issue | Deduct if able to fix |
| Compiler warnings | 2 point per issue, up to 8 points | |
| Linker errors | 3 points per issue | Deduct if able to fix |
| Valgrind errors | 2 points per issue, up to 8 points | |
| Leaked memory | 5 points | Flat deduction |

### Tests

Test case issues are more general and apply to the operation of the submitted programs.
If a student has lost a significant number of points, check to see if there's an issue with I/O that might be the cause.
That said, a problem in the actual program logic is assumed to be the student's fault.

| Infraction | Points | Notes |
|---|---|---|
| Incorrect I/O logic | 4 points | Try to fix briefly |
| Incorrect output format | 4 points | Try to fix or grade on correctness |
| Debug statements in output | 2 points | Regrade once removed |

### Style

Please make sure to check these issues and make a note of the deduction in the score report.
Additional deductions may be added if they don't fall under any of the following categories.

| Infraction | Points | Notes |
|---|---|---|
| Adding classes, members, or functions | 3 points | Only apply if explicitly disallowed |
| Exposing private members | 3 points | Only apply if explicitly disallowed |
| Global variables | 3 points | Always apply unless explicitly allowed |
| Combined header and implementation | 2 points | Always apply unless explicity allowed |
| Using namespaces in headers | 3 points | |
| Functions over 200 lines | 2 points | |
| Files over 500 lines | 2 points | |
| No comments | 2 points | Nontrivial classes, functions, and logical sections |
| Few comments | 1 point | Use above guidelines |
| Unreadable indentation | 2 points | No pattern or no indentation |
| Inconsistent indentation | 1 point | No uniformity in indentation levels |
| Commented code | 2 points | Acceptable as proof of work |
| Poor code quality | Up to 5 points | Includes repeated code, redundant logic, etc. |
