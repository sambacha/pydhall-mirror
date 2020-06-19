#! /usr/bin/env python
import gc
import sys
from timeit import repeat

from pydhall.parser import Dhall

def benchit(src, filename):
    NUMBER = 1
    REPEAT = 5
    gc.collect()
    total_seconds = min(repeat(lambda: Dhall.p_parse(src),
                               lambda: gc.enable(),
                               repeat=REPEAT,
                               number=NUMBER))
    seconds_each = total_seconds / NUMBER

    kb = len(src) / 1024.0

    print('%s: Took %.3fs to parse %.1fKB: %.0fKB/s' % (
        filename, seconds_each, kb, kb / seconds_each))
    return seconds_each

def _(input, expected):
    "dhall-lang/tests/parser/success/largeExpressionA.dhall"
    with open(input) as f:
        termA = Dhall.p_parse(f.read())

if __name__ == "__main__":
    input = "dhall-lang/tests/parser/success/largeExpressionA.dhall"
    with open(input) as f:
        benchit(f.read(), input)

    input = "dhall-lang/Prelude/JSON/renderAs"
    with open(input) as f:
        benchit(f.read(), input)
