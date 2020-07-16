from pydhall.parser import parse

from ._base import Schema
from .list_ import List, ListOf, MapOf
from .optional import Optional
from .primitive import Natural, Text, Bool, Primitive
from .record import Record, RecordLitValue
from .field import (
    BoolField,
    Field,
    ListField,
    ListOfField,
    MapOfField,
    NaturalField,
    Nested,
    RecordField,
    SimpleRenderer,
    TextField,
    UnionField,
)
from .union import Union, Alt
from .utils import SchemaVisitor, visitor


def load_src(cls, src):
    term = parse(src).resolve()
    # import ipdb; ipdb.set_trace()
    # print(term)
    assert term.type() @ cls._pydhall_type
    value = term.eval()
    return cls(value)


class GetLibraryVisitor(SchemaVisitor):
    def __init__(self):
        self.types = {}
        self.annon_unions = {}
        self.field_name = None

    def __call__(self, sh):
        self.visit(sh)
        return self.types

    @visitor(Record)
    def visit_record(self, r):
        type = r._pydhall_type
        default = {}
        for f in r._pydhall_fields:
            if f.default is not f.NoDefault:
                default[f.name] = f.type._pydhall_as_value(f.default)
        default = RecordLitValue(default)
        self.types[r.__name__] = RecordLitValue({"Type": type, "default": default})
        old_annons = self.annon_unions
        self.annon_unions = {}
        for f in r._pydhall_fields:
            self.visit(f)
        self.types[r.__name__].update(self.annon_unions)
        self.annon_unions = old_annons

    @visitor(UnionField)
    def visit_union_field(self, f):
        self.field_name = f.name
        self.visit(f.type)

    @visitor(Union)
    def visit_union(self, u):
        if isinstance(u, type):
            cls = u
        else:
            cls = u.__class__
        if cls.__name__ == "_anonUnion":
            self.annon_unions[self.field_name.capitalize()] = u._pydhall_type
        else:
            self.types[cls.__name__] = u._pydhall_type
        super().visit_union(u)


def get_library(cls):
    return GetLibraryVisitor()(cls)


class GetTypesVisitor(SchemaVisitor):
    def __init__(self):
        self.types = {}

    def __call__(self, sh):
        self.visit(sh)
        return self.types

    @visitor(Record)
    def visit_record(self, r):
        self.types[r.__name__] = r._pydhall_type
        super().visit_record(r)

    @visitor(Union)
    def visit_union(self, u):
        self.types[u.__class__.__name__] = u._pydhall_type
        super().visit_union(u)


def get_types(cls):
    return GetTypesVisitor()(cls)

__all__ = [
    "Alt",
    "Bool",
    "BoolField",
    "Field",
    "List",
    "ListField",
    "ListOf",
    "ListOfField",
    "MapOfField",
    "MapOf",
    "Natural",
    "NaturalField",
    "Nested",
    "Optional",
    "Primitive",
    "Record",
    "RecordField",
    "RecordLitValue",
    "Schema",
    "SimpleRenderer",
    "Text",
    "TextField",
    "Union",
    "UnionField",
    "get_library",
    "get_types",
    "load_src",
]
