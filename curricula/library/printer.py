import textwrap

class Printer:
    """Helper class for conveniently printing."""

    def __init__(self):
        self.buffer = []
        self.indentation = 0

    def print(self, *args, sep: str = " ", end: str = "\n", indentation: int = 0):
        """Standard print API."""

        self.buffer.append(textwrap.indent(sep.join(args), " " * (indentation + self.indentation)) + end)

    def indent(self, amount: int = 2):
        self.indentation += amount

    def dedent(self, amount: int = 2):
        self.indentation = max(0, self.indentation - amount)

    def __str__(self):
        return "".join(self.buffer)
