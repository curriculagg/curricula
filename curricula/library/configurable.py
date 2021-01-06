from typing import Any, Optional

from .inject import inject


class OrthogonalNone:
    """Custom none."""

    def __bool__(self):
        """Enable or default."""

        return False


none = OrthogonalNone()


def not_none(name: str, value: Any, default: Any = none) -> Any:
    """Return only if not none value."""

    if value is none:
        if default is not none:
            return default
        raise RuntimeError(f"can't find a valid source for {name}")
    return value


class Configurable:
    """Provide resolve on self."""

    @classmethod
    def getter_name(cls, field_name: str):
        return f"get_{field_name}"

    def __setattr__(self, key, value):
        """Don't allow overwriting with none."""

        if value is not none:
            super().__setattr__(key, value)

    def is_resolvable(
            self,
            field_name: str = None,
            field_getter_name: Optional[str] = none,
            local: Any = none) -> bool:
        """Determine whether one of the three is defined."""

        if local is not none:
            return True

        if field_name is not None and hasattr(self, field_name):
            return True

        if field_getter_name is none and field_name is not None:
            field_getter_name = Configurable.getter_name(field_name)
        if field_getter_name is not None and hasattr(self, field_getter_name):
            return True

        return False

    def resolve(
            self: Any,
            field_name: str = None,
            field_getter_name: Optional[str] = none,
            local: Any = none,
            default: Any = none,
            field_getter_resources: Optional[dict] = None) -> Any:
        """Check value, self.name, then self.get_name()."""

        if local is not none:
            return local

        # Check self
        if field_name is not None and hasattr(self, field_name):
            value = getattr(self, field_name)
            if value is not none:
                return value

        # Try getter
        if field_getter_name is none and field_name is not None:
            field_getter_name = Configurable.getter_name(field_name)

        if field_getter_name is not None and hasattr(self, field_getter_name):
            getter = getattr(self, field_getter_name)
            if callable(getter):
                if field_getter_resources is not None:
                    value = inject(field_getter_resources, getter)
                else:
                    value = getter()
                if value is not none:
                    return value

        # Return default if provided
        if default is not none:
            return default

        raise RuntimeError(f"can't find a valid source for {field_name or 'value'}")
