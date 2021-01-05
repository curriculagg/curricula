import abc
import argparse
from typing import Iterable, Dict

from ..library.importance import import_module

__all__ = (
    "PluginException",
    "Plugin",
    "PluginDispatcher",)


class PluginException(BaseException):
    """Base exception."""


class Plugin(abc.ABC):
    """All apps must meet these plugin criteria."""

    @classmethod
    def find(cls, module_name: str, name: str) -> "Plugin":
        """Import all exported plugins."""

        try:
            module = import_module(f"{module_name}.shell")
        except ImportError:
            return UnavailablePlugin(name)

        for declaration in vars(module).values():
            if isinstance(declaration, type) and issubclass(declaration, Plugin) and declaration.name == name:
                return declaration()
        return UnavailablePlugin(name)

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique plugin name."""

    @property
    @abc.abstractmethod
    def help(self) -> str:
        """Help text associated with command."""

    @abc.abstractmethod
    def setup(self, parser: argparse.ArgumentParser):
        """Create a sub-parser for the app."""

    @abc.abstractmethod
    def main(self, parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
        """Run if the build app is chosen."""


class UnavailablePlugin(Plugin):
    """Fallback for imported plugins that are not available."""

    name = "unavailable"
    help = "this plugin is not available"

    def __init__(self, name: str):
        self.name = name

    def setup(self, parser: argparse.ArgumentParser):
        pass

    def main(self, parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
        parser.error(f"the {self.name} plugin is unavailable")
        return -1


class PluginDispatcher(Plugin, abc.ABC):
    """A coordinator for plugins."""

    @property
    @abc.abstractmethod
    def plugins(self) -> Iterable[Plugin]:
        """List of plugin objects."""

    _key: str
    _plugins: Dict[str, Plugin]

    def __init__(self):
        """Compute some stuff."""

        super().__init__()
        self._plugins = {plugin.name: plugin for plugin in self.plugins}
        self._key = f"{self.name}:subcommand"

    def setup(self, parser: argparse.ArgumentParser):
        """Bind all plugins."""

        subparsers = parser.add_subparsers(required=True, dest=self._key, help=self.help)
        for plugin in self._plugins.values():
            plugin.setup(subparsers.add_parser(plugin.name, help=plugin.help))

    def main(self, parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
        """Dispatch."""

        return self._plugins[args[self._key]].main(parser, args)
