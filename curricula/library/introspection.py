from typing import Any


none = object()


def not_none(name: str, value: Any, none_value: Any = none, default_value: Any = none) -> Any:
    """Return only if not none value."""

    if value is none_value:
        if default_value is not none_value:
            return default_value
        raise RuntimeError(f"can't find a valid source for {name}")
    return value


def resolve(self: Any, name: str, none_value: Any = none, default_value: Any = none) -> Any:
    """Check value, self.name, then self.get_name()."""

    # Check self
    if hasattr(self, name):
        value = getattr(self, name)
        if value is not none_value:
            return value

    # Try getter
    getter_name = f"get_{name}"
    if hasattr(self, getter_name):
        getter = getattr(self, getter_name)
        if callable(getter):
            value = getter()
            if value is not none_value:
                return value

    # Return default if provided
    if default_value is not none:
        return default_value

    raise RuntimeError(f"can't find a valid source for {name}")
