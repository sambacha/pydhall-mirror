import os

from pydhall.schema import *


# Define the schema.
class SubConf1(Record):
    b = NaturalField(default=3)


class ListItemRecord(Record):
    c = NaturalField()


class U1(Union):
    Foo = Alt()
    Bar = Alt(Natural)


class Config(Record):
    a     = NaturalField(default=42)
    bool_ = BoolField(name="bool")
    sub   = RecordField(SubConf1)
    l     = ListOfField(Natural)
    l2    = ListOfField(Natural)
    l3    = ListOfField(ListItemRecord)
    l4    = ListOfField(SubConf1)
    l5    = ListOfField(Natural, default=[1])
    l6    = ListOfField(Natural, default=[])
    env   = TextField()
    u1    = Field(U1())
    u2    = UnionField(U1)
    u3    = UnionField({"A": Bool, "B": None})
    opt1  = Field(Optional(Natural))
    opt2  = Field(Optional(Natural))
    opt3  = NaturalField(optional=True)
    map1  = MapOfField(Natural)


class LibConfig(Record):
    r = RecordField(SubConf1)
    u = UnionField({"Foo": Bool, "Bar": None}, default={"Foo": True})


def test_dhall_library():
    cfg = load_src(LibConfig, """
        let test = pydhall+schema:pydhall.schema.tests.test_example::LibConfig
        in
        test.LibConfig::{
        , r = test.SubConf1::{=}
        -- , u = test.LibConfig.U.Foo True
        }
    """)
    assert cfg.r.b == 3


# TODO: le code typecheck alors que Config est un Schema Dhall.
def test_all_features():
    # Parse the user's configuration
    os.environ["PYDHALL_SCHEMA_TEST"] = "prod"

    cfg = load_src(Config, """
let test = pydhall+schema:pydhall.schema.tests.test_example::Config
in  test.Config::{
    , a = 1
    , bool = False
    , sub = { b = 3 }
    , l = []: List Natural
    , l2 = [1,2]
    , l3 = [{c = 42}]
    , l4 = [{b = 4}, {b = 5}]
    , env = env:PYDHALL_SCHEMA_TEST as Text
    , u1 = test.U1.Foo
    , u2 = test.U1.Bar 5
    , u3 = test.Config.U3.A True
    , opt1 = None Natural
    , opt2 = Some 2
    , opt3 = Some 6
    , map1 = toMap { k = 2 }
    } : test.Config
    """)

    # use it
    assert cfg.a == 1
    assert cfg.bool_ == False
    assert cfg.sub.b == 3
    assert cfg.l == []
    assert cfg.l2 == [1,2]
    assert cfg.l3[0].c == 42
    assert cfg.l4[0].b == 4
    assert cfg.l4[1].b == 5
    assert cfg.l5 == [1]
    assert cfg.l6 == []
    assert cfg.env == "prod"
    assert cfg.u1.name == "Foo"
    assert cfg.u1.value == None
    assert cfg.u2.name == "Bar"
    assert cfg.u2.value == 5
    assert cfg.opt1 == None
    assert cfg.opt2 == 2
    assert cfg.opt3 == 6
    assert cfg.map1["k"] == 2
