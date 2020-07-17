import pydhall.core.builtins
from .base import Dhall
from .exceptions import DhallParseError

from fastidious.parser_base import ParserError

def parse(src):
    try:
        return Dhall.p_parse(src)
    except ParserError as e:
        e.__class__ = DhallParseError
        raise e


def parse_file(path):
    with open(path) as f:
        return parse(f.read())


__all__ = ["Dhall"]
