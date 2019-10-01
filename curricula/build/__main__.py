import argparse
from pathlib import Path

from . import build


parser = argparse.ArgumentParser()
parser.add_argument("path")

result = parser.parse_args()
build.build(Path(result.path))
