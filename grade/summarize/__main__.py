import os
import argparse
import json
from pathlib import Path

from . import TaskSummary, OverallSummary


parser = argparse.ArgumentParser()
parser.add_argument("reports", help="A directory containing reports")
args = parser.parse_args()

target = Path(args.reports).absolute()

overall = OverallSummary()
tasks = {}

for name in os.listdir(str(target)):
    with open(target.joinpath(name)) as file:
        data = json.load(file)

    setup = 1
    for result in data:
        if result["task"]["name"] not in tasks:
            task = result["task"]
            summary = tasks[task["name"]] = TaskSummary(task)
        else:
            summary = tasks[result["task"]["name"]]
            task = summary.task

        summary.total += 1
        summary.complete += 1 if result["complete"] else 0
        summary.passed += 1 if result["passed"] else 0

        if task["kind"] == "setup" and task["required"] and not (result["complete"] and result["passed"]):
            setup = 0

    overall.total += 1
    overall.setup += setup


def p(x, n):
    return f"{round(x / n * 100)}%, -{n - x}"


print(f"Total: {overall.total}")
print(f"Setup: {overall.setup} ({p(overall.setup, overall.total)})")
for task_name, summary in tasks.items():
    print(f"{task_name}:")
    print(f"  Complete: {summary.complete} ({p(summary.complete, overall.total)})")
    print(f"  Passed: {summary.passed} ({p(summary.passed, overall.total)})")
