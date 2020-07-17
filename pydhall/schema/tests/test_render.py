import os

from pydhall.schema import *
from pydhall.schema.render import render


# Define the schema.
class SubConf1(Record):
    b = NaturalField(default=3)


class SubConf2(Record):
    c = NaturalField(default=3)


class U1(Union):
    Foo = Alt()
    Bar = Alt(Natural)


class U2(Union):
    alt1 = Alt(SubConf1)
    alt2 = Alt(SubConf2)


class Config(Record):
    a = NaturalField(default=42)
    sub = RecordField(SubConf1)
    if_ = NaturalField(name="if")
    u1 = UnionField(U1)
    u2 = UnionField(U1)
    u3 = UnionField(U2)
    u4 = UnionField(U2, renderer=Nested("u4Type"))
    u5 = UnionField(U2, renderer=Nested("u5Type", "u5Value"))
    map1  = MapOfField(Natural)
    optmap1 = MapOfField(Natural, optional=True)
    optmap2 = MapOfField(Natural, optional=True)
    optmap3 = MapOfField(Natural, optional="omitNone")
    optmap4 = MapOfField(Natural, optional=True, default=None)
    optmap5 = MapOfField(Natural, optional=True, default={"j": 5})


def test_simple_render1():
    cfg = load_src(Config, """
        let test = pydhall+schema:pydhall.schema.tests.test_render::Config
        in
        test.Config::{
        , a = 1
        , sub = test.SubConf1::{=}
        , `if` = 2
        , u1 = test.U1.Bar 1
        , u2 = test.U1.Foo
        , u3 = test.U2.alt2 { c = 2 }
        , u4 = test.U2.alt2 { c = 3 }
        , u5 = test.U2.alt2 { c = 4 }
        , map1 = toMap { k = 2 }
        , optmap1 = Some ( toMap { i = 3 } )
        , optmap2 = None ( List { mapKey: Text, mapValue: Natural })
        , optmap3 = None ( List { mapKey: Text, mapValue: Natural })
        }
        """)

    result = render(cfg)
    assert result == {
        "a": 1,
        "sub": { "b": 3 },
        "if": 2,
        "u1": 1,
        "u2": "Foo",
        "u3": { "c": 2 },
        "u4": {"u4Type": "alt2", "c": 3},
        "u5": {"u5Type": "alt2", "u5Value": {"c": 4}},
        "map1": {"k": 2},
        "optmap1": {"i": 3},
        "optmap2": None,
        "optmap4": None,
        "optmap5": {"j": 5},
    }


class U3(Union):
    List = Alt(ListOf("_anonList", Natural))

class Config2(Record):
    lst = UnionField(U3, default={"List": []})
    lst2 = UnionField(U3, default={"List": [1,2]})
    lst3 = UnionField(U3, default={"List": [1,2]})


def test_regression_default_list_in_union():
    cfg = load_src(Config2, """
        let test = pydhall+schema:pydhall.schema.tests.test_render::Config2
        in
        test.Config2::{
          , lst3 = test.U3.List [1,3]
        }
    """)
    assert cfg.lst.value == []
    result = render(cfg)
    assert result == {
        "lst": [],
        "lst2": [1, 2],
        "lst3": [1, 3],
    }
