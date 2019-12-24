import logging
import argparse

log = logging.getLogger("curricula")
log.propagate = False
log.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%m/%d/%y %I:%M:%S %p")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)


def add_logging_arguments(parser: argparse.ArgumentParser):
    """Add standard options for the logger."""

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", default=False)
    group.add_argument("-q", "--quiet", action="store_true", default=False)
    parser.add_argument("-l", "--log", default=None)


def handle_logging_arguments(args: argparse.Namespace) -> int:
    """Configure the logger according to arguments."""

    if args.verbose:
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        log.setLevel(logging.WARNING)

    if args.log:
        handler_stream = logging.FileHandler(args.log)
        log.addHandler(handler_stream)

    return 0
