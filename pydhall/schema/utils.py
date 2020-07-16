from ._base import Schema
from .record import Record
from .union import Union, Alt
from .field import Field
from .primitive import Primitive
from .optional import Optional
from .list_ import List


class visitor:
    def __init__(self, *cls):
        self.cls = cls

    def __call__(self, fn):
        fn._visitor_class = self.cls
        return fn


class SchemaVisitor:
    _visitor = None

    def __init_subclass__(cls,**kwargs):
        super().__init_subclass__(**kwargs)
        cls._visitor = {}
        for name in dir(cls):
            attr = getattr(cls, name)
            if hasattr(attr, "_visitor_class"):
                for target in attr._visitor_class:
                    cls._visitor[target] = attr

    def visit(self, sh):
        key = None
        try:
            if sh in self._visitor:
                key = sh
        except TypeError:  # probably a dict or a list
            pass
        if key is None:
            if isinstance(sh, type):
                tp = sh
            else:
                tp = sh.__class__
            for cls in tp.__mro__[:-1]:
                if cls in self._visitor:
                    key = cls
                    break
        method = self._visitor.get(key, self.__class__.visit_generic)
        return method(self, sh)

    @visitor(Record)
    def visit_record(self, r):
        for f in r._pydhall_fields:
            self.visit(f)

    @visitor(Field)
    def visit_field(self, f):
        self.visit(f.type)

    @visitor(Union)
    def visit_union(self, u):
        for a in u._pydhall_alternatives:
            if a.type is not None:
                self.visit(a.type)

    @visitor(List)
    def visit_list(self, l):
        self.visit(l._pydhall_item_type)

    @visitor(Optional)
    def visit_optional(self, o):
        self.visit(o.type)

    def visit_generic(self, sh):
        return None
