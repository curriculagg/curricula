import inspect

from typing import Callable, TypeVar

__all__ = ("inject",)

T = TypeVar("T")


def inject(resources: dict, function: Callable[[None], T]) -> T:
    """Inject resources into the function by name."""

    dependencies = {}
    for name, parameter in inspect.signature(function).parameters.items():
        dependency = resources.get(name, parameter.default)
        if dependency == parameter.empty:
            raise ValueError(f"could not satisfy dependency {name}")
        dependencies[name] = dependency
    return function(**dependencies)
