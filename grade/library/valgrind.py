import os
from xml.etree.ElementTree import Element, parse
from typing import Optional, List, TextIO
from dataclasses import dataclass, field

from . import process

VALGRIND_ARGS = ("valgrind", "--tool=memcheck", "--leak-check=yes", "--xml=yes")
VALGRIND_XML_FILE = "valgrind.xml"


def run(*args: str, timeout: float) -> Optional[Element]:
    """Run valgrind on the program and return IR count."""

    runtime = process.run(*VALGRIND_ARGS, f"--xml-file={VALGRIND_XML_FILE}", *args, timeout=timeout)
    if os.path.exists(VALGRIND_XML_FILE):
        errors = []
        with open(VALGRIND_XML_FILE) as file:
            root = parse(file).getroot()
        os.remove(VALGRIND_XML_FILE)
        return root
    return None
