import re
import contextlib
from typing import TextIO, Dict, Callable, Any
from pathlib import Path


class WriterItemize:
    """Context for managing a list generator."""

    file: TextIO

    def __init__(self, file: TextIO):
        """Just use the file of the document."""

        self.file = file

    def add(self, item: str):
        """Add a bullet to the document."""

        self.file.write("- {}".format(item.strip()))


class WriterEnumerate:
    """Context for managing an enumeration generator."""

    file: TextIO
    counter: int

    def __init__(self, file: TextIO, counter: int = 1):
        """Just use the file of the document."""

        self.file = file
        self.counter = counter

    def add(self, item: str):
        """Add a bullet to the document."""

        self.file.write("{}. {}".format(self.counter, item.strip()))
        self.counter += 1


class Writer:
    """A loose wrapper for a Markdown document."""

    file: TextIO

    def __init__(self, file: TextIO):
        """Initialize a new Markdown document."""

        self.file = file

    def __enter__(self):
        """Enter in a with statement."""

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the file once done."""

        self.file.close()

    def add(self, section: str):
        """Add a section to the document, strip whitespace."""

        self.file.write(section.strip() + "\n\n")

    def add_header(self, contents: str, *, level: int = 1):
        """Add a header section."""

        self.add("{} {}".format("#" * level, contents))

    def add_front_matter(self, **kwargs):
        """Add a front matter header in YAML format."""

        lines = tuple("{}: {}".format(key, value) for key, value in kwargs.items())
        self.add("\n".join(("---",) + lines + ("---",)))

    @contextlib.contextmanager
    def start_itemize(self):
        """Open an itemizing context, resulting in a bulleted list."""

        yield WriterItemize(self.file)
        self.add("\n\n")

    @contextlib.contextmanager
    def start_enumerate(self):
        """Open an itemizing context, resulting in a bulleted list."""

        yield WriterEnumerate(self.file)
        self.add("\n\n")


INTERPOLATION_PATTERN = re.compile(r"(?<!\\)" r"\[\[\s*" r"(.+?)" r"\s*\]\]")

NAMESPACE = {}

FILTERS = {
    "datetime": lambda d: d.strftime("%B %d, %Y at %H:%M"),
    "date": lambda d: d.strftime("%B %d, %Y"),
    "str": lambda x: str(x),
}


def underwrite(top: dict, bottom: dict) -> dict:
    """Add any keys not in bottom to top, return top."""

    for key in bottom:
        if key not in top:
            top[key] = bottom[key]
    return top


def get(obj, *keys):
    """Descend a list of string properties."""

    for key in keys:
        obj = obj[key] if hasattr(obj, "__getitem__") else getattr(obj, key)
    return obj


class Template:
    """Tools for manipulating a Markdown template."""

    contents: str

    def __init__(self, file: TextIO):
        """Load a Markdown template from a path."""

        self.contents = file.read()

    def interpolate(self, namespace: Dict[str, Any], filters: Dict[str, Callable[[Any], Any]] = None) -> str:
        """Interpolate the file with values and filters."""

        contents = self.contents
        namespace = underwrite(namespace, NAMESPACE)
        filters = underwrite(filters, FILTERS) if filters is not None else {}

        matches = list(INTERPOLATION_PATTERN.finditer(contents))
        for match in reversed(matches):
            variable_name, *filter_names = map(str.strip, match.group().split("|"))
            result = get(namespace, variable_name.split("."))
            for filter_name in filter_names:
                result = filters[filter_name](result)
            contents = contents[:match.start()] + str(result) + contents[match.end():]
        return contents
