from typing import Any, Optional


none = object()


def not_none(name: str, value: Any, none_value: Any = none, default_value: Any = none) -> Any:
    """Return only if not none value."""

    if value is none_value:
        if default_value is not none_value:
            return default_value
        raise RuntimeError(f"can't find a valid source for {name}")
    return value


def resolve(
        self: Any,
        field_name: str = None,
        field_getter_name: Optional[str] = none,
        local_value: Any = none,
        none_value: Any = none,
        default_value: Any = none) -> Any:
    """Check value, self.name, then self.get_name()."""

    if local_value is not none_value:
        return local_value

    # Check self
    if field_name is not None and hasattr(self, field_name):
        value = getattr(self, field_name)
        if value is not none_value:
            return value

    # Try getter
    if field_getter_name is none and field_name is not None:
        field_getter_name = f"get_{field_name}"

    if field_getter_name is not None and hasattr(self, field_getter_name):
        getter = getattr(self, field_getter_name)
        if callable(getter):
            value = getter()
            if value is not none_value:
                return value

    # Return default if provided
    if default_value is not none:
        return default_value

    raise RuntimeError(f"can't find a valid source for {field_name or 'value'}")
