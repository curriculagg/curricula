

@dataclass
class ValgrindWhat:
    """Explanation of error, can have dynamic tags."""

    text: str
    fields: dict = field(default_factory=dict)

    @classmethod
    def load(cls, element: Element) -> "ValgrindWhat":
        """Load either what or xwhat."""

        if element.tag == "what":
            return ValgrindWhat(element.text)
        else:
            text = ""
            fields = dict()
            for child in element:
                if child.tag == "tag":
                    text = child.text
                else:
                    fields[child.tag] = child.text
            return ValgrindWhat(text, fields)


@dataclass
class ValgrindError:
    """Represents an error tag from a Valgrind XML report."""

    unique: int
    tid: int
    kind: str
    what: ValgrindWhat

    @classmethod
    def load(cls, element: Element) -> "ValgrindError":
        """Load an error from an element."""

        unique = int(element.find("unique").text, 16)
        tid = int(element.find("tid").text)
        kind = element.find("kind").text
        what = ValgrindWhat.load(element.find("what") or element.find("xwhat"))
        return cls(unique, tid, kind, what)


@dataclass
class ValgrindReport:
    """Include data about memory lost and errors."""

    runtime: process.Runtime
    errors: Optional[List[ValgrindError]] = None

    def memory_lost(self):
        """Count up bytes and blocks lost."""

        leaked_bytes = 0
        leaked_blocks = 0
        for error in self.errors:
            if error.kind in ("Leak_DefinitelyLost", "Leak_IndirectlyLost", "Leak_PossiblyLost"):
                leaked_bytes += int(error.what.fields["leakedbytes"])
                leaked_blocks += int(error.what.fields["leakedblocks"])
        return leaked_bytes, leaked_blocks
