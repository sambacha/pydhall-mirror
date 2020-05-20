"""Main module."""

from pydhall.parser import Dhall


def load(fp):
    src = fp.read()
    print(src)
    return loads(src)
    

def loads(s):
    result = Dhall.p_parse(s)
    result.type()
    return result
