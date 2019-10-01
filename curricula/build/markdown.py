def header(contents: str, *, level: int = 1, newline: int = 2):
    return "{} {}{}".format("#" * level, contents, "\n" * newline)


def front_matter(**kwargs):
    return "\n".join(
        ("---",) +
        tuple("{}: {}".format(key, value) for key, value in kwargs.items()) +
        ("---",)
    ) + "\n\n"
