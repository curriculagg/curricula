"""A simple output formatter.

Provides wrapped access to output to allow for middleware such as
continued indentation, line numbers, etc.
"""


class Printer:
    """Intended for use as an instance."""

    _indent: int = 0
    _ended: bool = True

    def indent(self, size=2):
        assert size > 0
        self._indent += size

    def dedent(self, size=2):
        assert size > 0
        self._indent = max(self._indent - size, 0)

    def reset(self):
        self._indent = 0

    def __call__(self, line: str, end: bool = True):
        """Print a line to standard out."""

        if self._ended:
            line = " " * self._indent + line
        print(line, end="\n" if end else "")
        self._ended = end


class AsyncPrinter(Printer):
    """A printer that consumes calls until run."""


