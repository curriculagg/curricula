import abc
import argparse


class PluginException(BaseException):
    """Base exception."""


class Plugin(abc.ABC):
    """All apps must meet these plugin criteria."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Apps must be uniquely named."""

    @property
    @abc.abstractmethod
    def help(self) -> str:
        """Apps must be uniquely named."""

    @classmethod
    @abc.abstractmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Create a subparser for the app."""

    @classmethod
    @abc.abstractmethod
    def main(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Run if the build app is chosen."""
