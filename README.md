# Curricula

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e6d63124ef0c4a939f726c1609841978)](https://www.codacy.com/manual/csci104/curricula?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=csci104/curricula&amp;utm_campaign=Badge_Grade)

Curricula is a set of specifications and tools for managing content and grading assignments in a college-level computer science setting.
It is currently being developed by [Noah Kim](https://noahbkim.github.io) for CSCI 104, the most challenging core-track C++ course at USC for CS majors.

## How Does it Work?

Curricula covers the two main aspects of managing assignments for a programming course.

1. **Assignment creation**: Curricula provides a schema for developing assignments per-problem rather than all at once.
   This allows content producers to easily port assignments from previous semesters to the evolving parameters of the current.
   Assignments can then be built up from their components problems, separating each and combining their independent parts into packages for publishing, grading, etc.

2. **Submission grading**: the other function of Curricula is to provide a robust framework for testing all aspects of submitted code.
   This includes checks for things like correctness, time complexity, resources leakage, and even code style, all while facilitating granular configuration.
   These tests are written to a universal output format so that they can be reinterpreted without having to re-run the code. 

## Build

The assignment builder works on an assignment bases, with build targets being full, individual assignments composed of problems.

### Writing an Assignment

Assignments consist of a set of general instructions and a schema.
An example can be found in [example/assignment/](example/assignment).
Problems can be specified inside or outside of an assignment's directory.
The `assignment.json` file must include the following fields:

- `title` provides a full title of the assignment.
- `authors` is a list of objects containing a `name` and `email`.
- `dates` is an object containing two fields, `assigned` and `due`, with dates formatted as strings `YYYY-MM-DD HH:MM`.
- `problems` is a list of objects containing a relative `path` to each problem directory and a `percentage` representing its weight in the assignment.
  Note that problems are included in the instructions (and other composite documents) in the order of this list.
  Consider the item in the example that includes the `hello_world` problem, noting that `0.1` corresponds to 10%:

```json
{
  "path": "problem/hello_world",
  "percentage": 0.1
}
```

### Writing a Problem

Problems contain the bulk of the content.
An example can be found in [example/assignment/problem/hello_world/](example/assignment/problem/hello_world).
Problems also use a schema for metadata.
The `problem.json` file must include the following fields:

- `title` provides a full title of the problem
- `authors` is a list of objects containing a `name` and `email`.
- `grading` is an object that contains the estimated number of `minutes` required to grade manually and three boolean flags for how the problem is graded: `automated`, `review`, and `manual`.

Optionally, `problem.json` may also include:

- `topics` is a list of string tags that may eventually be used to search through a catalog of problems.

In addition to the schema, problems also consist of the following components:

1. Problems **instructions** are specified in the `README.md` of the problem.
   Instructions are made available for embedding in the templating phase of the build process.
   Typically, the compiled instructions for an assignment will consist of the general instructions followed by the title, weight, and instructions for each specific problem.
   Any assets, such as images, can be placed in an `assets/` folder and will be provided alongside the composite instructions.

2. Problem **resources**, placed in a `resources/` directory, are where any skeleton code for the problem can be provided to students.
   The resources directory for each problem is copied into a combined resources folder in the compiled assignment.

3. A **solution** may also be provided along with each problem in `solution/`.
   The solution is kept separate from other files, but can be provided to TAs and graders.
   Similarly to the instructions, any provided `README.md` files in the `solution/` directory are merged into a cumulative solution document for the entire submission.
   It is encouraged that material writers use this functionality for assignment cheat sheets, or explanations of common solution methods.
   
4. The **grading** tools for a problem may be included in the `grading/` directory.
   If automated grading is enabled in the problem, the builder will look for a `tests.py` that uses the `curricula.shortcuts.Grader`.
   If a `README.md` is provided, it will be merged into a cumulative grading document for the entire submission.
   This can be used to build a custom rubric for each problem.
   
### Templates

The builder also requires a set of templates to compose assignments with.
These templates are the glue for the instruction, solution, and grading `README.md` files.
The following templates are required, but feel free to refer to or use wholesale the [examples](example/template/build).

```
template/
  build/
    instructions/
      assignment.md
      problem.md
    solution/
      assignment.md
      problem.md
    grading/
      assignment.md
      problem.md
```

### Distribution and Grading

After using `curricula` to build an assignment, the resultant composite artifacts will be ready for use.
Mostly, this involves distributing the instructions, resources, and solutions to the right parties.
However, `curricula` also provides facilities for grading submissions.

## Grade

Grading is the other half of `curricula`'s core functionality.
In order to use automated grading, material writers have to implement tests using `curricula.grade`'s toolkit.

### Writing Tests

While somewhat bulkier than unit-test frameworks, the additional mechanisms backing the `Grader` make it much easier to generate and manage reports for students.
Let's walk through an [example](example/assignment/problem/hello_world/grading/tests.py).

```python
from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.check.common import check_file_exists
from curricula.grade.setup.build.common import build_gpp_executable
from curricula.library import files

GPP_OPTIONS = ("-Wall", "-std=c++11")

grader = Grader()
````

To start off, we include `pathlib` for convenient, file-system-independent path operations.
We also include several utilities from `curricula` and define `g++` command line options we'll use later.
Finally, we'll initialize the grader for this problem.

```python
@grader.setup.check(sanity=True)
def check_hello_world(context: Context, resources: dict):
    """Check whether hello_world.cpp has been submitted."""

    resources["hello_world_source_path"] = context.problem_directory.joinpath("hello_world.cpp")
    return check_file_exists(resources["hello_world_source_path"])
```

Here, we register a `check` task in the `setup` phase of the grader.
The `sanity` option indicates that if we run grading on a submission with `--sanity`, this task will be run.
Note that parameters in tasks are injected, but can also be accessed manually through the `resources` dictionary (`resources['resources'] is resources`).
In this task, we store the source path of file we're expecting to grade for this problem.
However, if it doesn't exist, the returned `CorrectnessResult` will indicate to the grader that this task has failed, and that any dependent tasks should not be executed.

```python
@grader.setup.build(dependency="check_hello_world", sanity=True)
def build_hello_world(hello_world_source_path: Path, resources: dict):
    """Compile the program with gcc."""

    resources["hello_world_path"] = Path("/tmp", "hello_world")
    result, resources["hello_world"] = build_gpp_executable(
        source_path=hello_world_source_path,
        destination_path=resources["hello_world_path"],
        gpp_options=GPP_OPTIONS)
    return result
```

This segment builds the submitted `hello_world.cpp` file with `g++`.
As specified by the registration decorator, this task depends on `check_hello_world` passing.
If a task has multiple dependencies, `dependencies=["check_hello_world", ...]` may be used instead.
In the task method, a custom `ExecutableFile` will be inserted into `resources`, and the `BuildResult` from the build function will be returned to the grader.
Note that both [`build_gpp_exectuable`](curricula/grade/setup/build/common.py) and [`check_file_exists`](curricula/grade/setup/check/common.py) are just convenience methods that reduce code.

```python
@grader.test.correctness(dependency="build_hello_world")
def test_hello_world_output(hello_world: ExecutableFile):
    """Check if the program outputs as expected."""

    runtime = hello_world.execute(timeout=1)
    return CorrectnessResult(passed=runtime.stdout.strip() == b"Hello, world!", runtime=runtime.dump())
```

This is an actual test cases.
In a proper problem, there will most likely be many more of these.
Note that since there's no `sanity=True` in the registration decorator, this test will not be run if the grader is sanity-checking a solution.
Here, we simply invoke the built binary `hello_world`.
If what's outputted to `stdout` during its runtime is `"Hello, world!"`, the `CorrectnessResult` will indicate the case passed.

For an individual problem, this whole harness might seem somewhat bulky.
However, note that the registration decorator can be used inline to register a generated task.
In other words, test cases that simply compare input and output files can simply be dynamically registered with a for loop rather than be written out manually.

```python
@grader.teardown.cleanup(dependency="build_hello_world")
def cleanup_hello_world(hello_world_path: Path):
    """Clean up executables."""

    if hello_world_path.is_file():
        files.delete_file(hello_world_path)
````

In this last segment, the built binary is deleted.
Not returning a result in a task registered in the `teardown` phase will cause the grader to generate a default `TeardownResult` with a passing status.
Note that `build_hello_world`, `test_hello_world_output`, and `cleanup_hello_world` all depend on `build_hello_world`.
If the latter does not pass, neither will any of the former.

## Grader Output

Grading an assignment will yield a serializable `AssignmentReport`, which is composed of `ProblemReport` objects for each problem graded automatically.
For the `hello_world` solution, the following report was generated.

```json
{
  "hello_world": {
    "check_hello_world": {
      "complete": true,
      "passed": true,
      "task": "check_hello_world",
      "details": {}
    },
    "build_hello_world": {
      "complete": true,
      "passed": true,
      "task": "build_hello_world",
      "details": {
        "runtime": {
          "args": [
            "g++",
            "-Wall",
            "-std=c++11",
            "-o",
            "/tmp/hello_world",
            "artifacts/assignment/solution/hello_world/hello_world.cpp"
          ],
          "timeout": null,
          "code": 0,
          "elapsed": 0.21283740003127605,
          "stdin": null,
          "stdout": "",
          "stderr": "",
          "timed_out": false,
          "raised_exception": false,
          "exception": null
        }
      }
    },
    "test_hello_world_output": {
      "complete": true,
      "passed": true,
      "task": "test_hello_world_output",
      "details": {
        "runtime": {
          "args": [
            "/tmp/hello_world"
          ],
          "timeout": 1,
          "code": 0,
          "elapsed": 0.0011609999928623438,
          "stdin": null,
          "stdout": "Hello, world!\n",
          "stderr": "",
          "timed_out": false,
          "raised_exception": false,
          "exception": null
        }
      }
    },
    "cleanup_hello_world": {
      "complete": true,
      "passed": true,
      "task": "cleanup_hello_world",
      "details": {}
    }
  }
}
```

Note that this report matches up key-wise with the grading artifact `grading.json` file:

```json
{
  "hello_world": {
    "title": "Hello, World!",
    "directory": "hello_world",
    "percentage": 0.1,
    "tasks": {
      "check_hello_world": {
        "name": "check_hello_world",
        "description": "Check whether hello_world.cpp has been submitted.",
        "stage": "setup",
        "kind": "check",
        "dependencies": [],
        "details": {
          "sanity": true
        }
      },
      "build_hello_world": {
        "name": "build_hello_world",
        "description": "Compile the program with gcc.",
        "stage": "setup",
        "kind": "build",
        "dependencies": [
          "check_hello_world"
        ],
        "details": {
          "sanity": true
        }
      },
      "test_hello_world_output": {
        "name": "test_hello_world_output",
        "description": "Check if the program outputs as expected.",
        "stage": "test",
        "kind": "correctness",
        "dependencies": [
          "build_hello_world"
        ],
        "details": {}
      },
      "cleanup_hello_world": {
        "name": "cleanup_hello_world",
        "description": "Clean up executables.",
        "stage": "teardown",
        "kind": "cleanup",
        "dependencies": [
          "build_hello_world"
        ],
        "details": {}
      }
    }
  }
}
```

Using these two data sources, the grader can format each report into a readable file.
This functionality is provided in the `tools` package of `curricula.grade`.

## Using Curricula

Curricula can be used by installing the [command line interface](https://github.com/csci104/curricula-shell).
This repository only contains the core functionality. 
