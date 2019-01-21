"""A simple output formatter.

Provides wrapped access to output to allow for middleware such as
continued indentation, line numbers, etc.
"""


class Printer:
    """Intended for use as an instance."""

    _indent: int = 0
    _lineno: int = None
    _ended: bool = True

    def indent(self, size=2):
        assert size > 0
        self._indent += size

    def dedent(self, size=2):
        assert size > 0
        self._indent = max(self._indent - size, 0)

    def reset(self):
        self._indent = 0

    def __pos__(self):
        self.indent()

    def __neg__(self):
        self.dedent()

    def __invert__(self):
        self.reset()

    def __call__(self, line: str, end: bool = True):
        """Print a line to standard out."""

        if self._ended:
            line = " " * self._indent + line
            if self._lineno is not None:
                line = "{:-3}. " + line

        print(line, end="\n" if end else "")

        self._ended = end
