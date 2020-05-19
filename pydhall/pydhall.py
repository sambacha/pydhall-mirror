"""Main module."""

from pydhall.parser import Dhall


def loads(src):
    result = Dhall.p_parse(src)
    result.type()
    return result
