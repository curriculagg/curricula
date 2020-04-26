import inspect


def get_source_location(stack_level: int = 1) -> str:
    caller = inspect.getframeinfo(inspect.stack()[stack_level][0])
    return f"{caller.filename}:{caller.lineno}"
