def truncate(string: str, length: int, append: str = "...") -> str:
    """Shorthand for cutting off long strings.

    If length is zero or negative, the string will not be checked or
    truncated. The original string will be returned.
    """

    if len(string) > length > 0:
        return string[:length - len(append)] + append
    return string
