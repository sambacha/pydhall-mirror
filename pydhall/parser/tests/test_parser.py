#!/usr/bin/env python

"""Tests for `pydhall` package."""

from urllib.parse import urlparse
from math import inf, nan

import pytest

from pydhall.ast.nodes import (
    BlockComment,
    DoubleLit,
    LineComment,
    TextLit,
    Var,
)

from pydhall.parser import Dhall


def test_char_classes():
    p = Dhall("Ā1")
    result = p.ValidNonAscii()
    assert result == "Ā"


def test_line_comment():
    p = Dhall("-- hello\nlet foo = 1 in foo")
    result = p.LineComment()
    assert result == LineComment(" hello", offset=0)
    p = Dhall("--\nlet foo = 1 in foo")
    result = p.LineComment()
    assert result == LineComment("", offset=0)


def test_block_comment():
    p = Dhall("{- hop -}")
    result = p.BlockComment()
    assert result == BlockComment("{- hop -}", offset=0)


def test_label():
    p = Dhall("label")
    result = p.Label()
    assert p.p_flatten(result) == "label"
    p = Dhall("iflabel")
    result = p.Label()
    assert p.p_flatten(result) == "iflabel"
    p = Dhall("if")
    result = p.Label()
    assert result is p.NoMatch
    p = Dhall("`label`")
    result = p.Label()
    assert p.p_flatten(result) == "label"
    p = Dhall("`if label`")
    result = p.Label()
    assert p.p_flatten(result) == "if label"
    p = Dhall("`if`")
    result = p.Label()
    assert p.p_flatten(result) == "if"


def test_url():
    p = Dhall("http://example.com/")
    result = p.HttpRaw()
    assert result == urlparse("http://example.com/")
    p = Dhall("https://user:pass@example.com/package.dhall?stuff=21&b=32")
    result = p.HttpRaw()
    assert result == urlparse(
        "https://user:pass@example.com/package.dhall?stuff=21&b=32")


def test_natural():
    p = Dhall("42")
    result = p.NaturalLiteral()
    assert result.value == 42
    p = Dhall("0xa1")
    result = p.NaturalLiteral()
    assert result.value == 161
    p = Dhall("0")
    result = p.NaturalLiteral()
    assert result.value == 0


def test_double_lit():
    p = Dhall("0.02")
    result = p.NumericDoubleLiteral()
    assert result == DoubleLit(value=0.02, offset=0)
    p = Dhall("+2e-2")
    result = p.NumericDoubleLiteral()
    assert result == DoubleLit(value=0.02, offset=0)
    p = Dhall("+2E-2")
    result = p.NumericDoubleLiteral()
    assert result == DoubleLit(value=0.02, offset=0)
    p = Dhall("-0.02")
    result = p.NumericDoubleLiteral()
    assert result == DoubleLit(value=-0.02, offset=0)
    p = Dhall("-0.02")
    result = p.DoubleLiteral()
    assert result == DoubleLit(value=-0.02, offset=0)
    p = Dhall("-Infinity")
    result = p.DoubleLiteral()
    assert result == DoubleLit(value=-inf, offset=0)
    p = Dhall("NaN")
    result = p.DoubleLiteral()
    assert result == DoubleLit(value=nan, offset=0)


def test_var():
    p = Dhall("myvar")
    result = p.Variable()
    assert result == Var("myvar", None, offset=0)
    p = Dhall("_@2")
    result = p.Variable()
    assert result == Var("_", 2, offset=0)


def test_double_quote_text():
    p = Dhall('"a string"')
    result = p.DoubleQuoteLiteral()
    assert result == TextLit(chunks=[], suffix='a string', offset=0)
    # TODO: add interpolations test
