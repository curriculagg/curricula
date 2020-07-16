import json
from pathlib import Path

from ...library.template import jinja2_create_environment

ROOT = Path(__file__).absolute().parent


RETURN = """<span class="punctuation">&crarr;</span><br>"""
SPACE = """<span class="punctuation">&middot;</span>"""


def show_whitespace(contents: str) -> str:
    return contents.replace(" ", SPACE).replace("\n", RETURN)


def out_from_runtime_stdout(report: dict) -> str:
    return report["runtime"]["stdout"]


def compare_output(template_path: Path, report_path: Path) -> str:
    """Generate a comparison of the expected output."""

    with report_path.open() as file:
        reports = json.load(file)

    environment = jinja2_create_environment(custom_template_path=template_path)
    difference_template = environment.get_template("template:grade/compare/difference.html")
    compare_template = environment.get_template("template:grade/compare/compare.html")

    content = f"<h1>{report_path.parts[-1]}</h1>\n<p>Correct on left, student on right</p>\n"
    for problem_short, report in reports.items():
        content += f"<h2><code>{problem_short}</code></h2>"
        for task_name, result in report.items():
            if result["complete"] and not result["passed"] and "error" in result:
                expected = result["error"]["expected"]
                if isinstance(expected, str):
                    expected = [expected]
                if expected is None:
                    expected = []
                received = result["error"]["received"]

                expected = list(map(show_whitespace, expected))
                received = show_whitespace(received) if received is not None else ""
                content += difference_template.render(task_name=task_name, expected=expected, received=received)

    return compare_template.render(content=content)
