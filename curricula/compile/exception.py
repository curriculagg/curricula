class CompilationException(Exception):
    """Raised during target or unit compilation."""

    message: str

    def __init__(self, message: str):
        self.message = message
