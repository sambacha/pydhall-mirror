from pydhall.utils import Visitor, visitor

from ._base import Schema
from .record import Record
from .union import Union, Alt
from .field import Field
from .primitive import Primitive
from .optional import Optional
from .list_ import List


class SchemaVisitor(Visitor):

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
