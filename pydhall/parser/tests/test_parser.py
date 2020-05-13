#!/usr/bin/env python

"""Tests for `pydhall` package."""

from urllib.parse import urlparse
from math import inf, nan

import pytest

from pydhall.ast.nodes import (
    Binding,
    BlockComment,
    DoubleLit,
    IntegerLit,
    Let,
    LineComment,
    NaturalLit,
    PlusOp,
    TextLit,
    TimesOp,
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


@pytest.mark.parametrize("input,expected", [
    ("label", "label"),
    ("iflabel", "iflabel"),
    ("`label`", "label"),
    ("`if label`", "if label"),
    ("`if`", "if"),
])
def test_label(input, expected):
    p = Dhall(input)
    result = p.Label()
    assert p.p_flatten(result) == expected


@pytest.mark.parametrize("input", [
    ("if",)
])
def test_label_fail(input):
    p = Dhall(input)
    result = p.Label()
    assert result is p.NoMatch


def test_url():
    p = Dhall("http://example.com/")
    result = p.HttpRaw()
    assert result == urlparse("http://example.com/")
    p = Dhall("https://user:pass@example.com/package.dhall?stuff=21&b=32")
    result = p.HttpRaw()
    assert result == urlparse(
        "https://user:pass@example.com/package.dhall?stuff=21&b=32")


@pytest.mark.parametrize("input,expected", [
    ("42", NaturalLit(value=42, offset=0)),
    ("0", NaturalLit(value=0, offset=0)),
    ("161", NaturalLit(value=161, offset=0)),
])
def test_natural(input, expected):
    p = Dhall(input)
    result = p.NaturalLiteral()
    assert result == expected


@pytest.mark.parametrize("input,expected", [
    ("0.02", DoubleLit(value=0.02, offset=0)),
    ("+2e-2", DoubleLit(value=0.02, offset=0)),
    ("+2E-2", DoubleLit(value=0.02, offset=0)),
    ("-0.02", DoubleLit(value=-0.02, offset=0)),
])
def test_numeric_double_lit(input, expected):
    p = Dhall(input)
    result = p.NumericDoubleLiteral()
    assert result == expected


@pytest.mark.parametrize("input,expected", [
    ("-0.02", DoubleLit(value=-0.02, offset=0)),
    ("-Infinity", DoubleLit(value=-inf, offset=0)),
    ("NaN", DoubleLit(value=nan, offset=0)),
])
def test_double_lit(input, expected):
    p = Dhall(input)
    result = p.DoubleLiteral()
    assert result == expected


@pytest.mark.parametrize("input,expected", [
    ("+42", IntegerLit(value=42, offset=0)),
    ("+0xa1", IntegerLit(value=161, offset=0)),
    ("+0", IntegerLit(value=0, offset=0)),
    ("-42", IntegerLit(value=-42, offset=0)),
    ("-0xa1", IntegerLit(value=-161, offset=0)),
    ("-0", IntegerLit(value=-0, offset=0)),
])
def test_integer_lit(input, expected):
    p = Dhall(input)
    result = p.IntegerLiteral()
    assert result == expected


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


@pytest.mark.parametrize("input,expected", [
    ("let a = 42 in a",
     Let(
        bindings=[
            Binding(
                variable='a',
                annotation='',
                value=NaturalLit(value=42, offset=0)
                , offset=0
            )
        ],
        body=Var(name='a', index=None, offset=0)
        , offset=0)),
])
def test_bindings(input, expected):
    p = Dhall(input)
    result = p.Bindings()
    assert result == expected


@pytest.mark.parametrize("input,expected", [
    ("1 + 2",
     PlusOp(
        l=NaturalLit(value=1, offset=0),
        r=NaturalLit(value=2, offset=0), offset=0)),
    ("1 + 2 + 3",
     PlusOp(
        l=PlusOp(
            l=NaturalLit(value=1, offset=0),
            r=NaturalLit(value=2, offset=0),
            offset=0),
        r=NaturalLit(value=3, offset=0),
        offset=0)),
    ("1 + 2 * 3",
     PlusOp(
        l=NaturalLit(value=1, offset=0),
        r=TimesOp(
            l=NaturalLit(value=2, offset=0),
            r=NaturalLit(value=3, offset=0),
            offset=0),
        offset=0)),
])
def test_operator_expr(input, expected):
    p = Dhall(input)
    result = p.OperatorExpression()
    assert result == expected
