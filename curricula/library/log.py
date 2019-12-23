import logging
import argparse

log = logging.getLogger("curricula")
log.propagate = False

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%m/%d/%y %I:%M:%S %p")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)


def add_logging_arguments(parser: argparse.ArgumentParser):
    """Add standard options for the logger."""

    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-l", "--log", default=None)


def handle_logging_arguments(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Configure the logger according to arguments."""

    if not 0 <= args.verbose <= 3:
        parser.error("verbosity level may be 0 through 3")
        return 1
    log.setLevel({0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG, 3: logging.NOTSET}[args.verbose])

    if args.log:
        handler_stream = logging.FileHandler(args.log)
        log.addHandler(handler_stream)

    return 0
