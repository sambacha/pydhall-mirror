from .utils import SchemaVisitor, visitor
from .record import Record, Field
from .list_ import List
from .union import Union, UnionAlternative
from .field import UnionField


class RenderVisitor(SchemaVisitor):
    def __init__(self):
        # stack of containters
        self.result = None
        self.current_record = None

    def emit(self, r):
        if self.result is None:
            self.result = r
        elif isinstance(self.result, list):
            self.result.append(r)

    @visitor(Record)
    def visit_record(self, r):
        old_result = self.result
        old_record = self.current_record
        self.current_record = r
        result = {}
        for f in r._pydhall_fields:
            # import ipdb; ipdb.set_trace()
            self.result = None
            self.visit(f)
            self.result(result)
        self.result = old_result
        self.current_record = old_record
        self.emit(result)

    @visitor(Field)
    def visit_field(self, f):
        u = f.__get__(self.current_record)
        self.visit(u)
        result = self.result
        if result is None and f.optional == "omitNone":
            def add_field(r):
                return
        else:
            def add_field(r):
                r[f.name] = result
        self.result = add_field

    @visitor(UnionField)
    def visit_unionfield(self, f):
        u = f.__get__(self.current_record)
        if u is None:
            if f.optional == "omitNone": 
                def add_union(r):
                    return
            else:
                def add_union(r):
                    r[f.name] = None
        else:
            self.visit(u)
            result = self.result
            def add_union(r):
                f.renderer(u.alt.name, result, f.name, r)
        self.result = add_union

    @visitor(UnionAlternative)
    def visit_alternative(self, a):
        self.visit(a.value)

    @visitor(list)
    def visit_list(self, l):
        old_result = self.result
        result = []
        for i in l:
            self.result = None
            self.visit(i)
            result.append(self.result)
        self.result = old_result
        self.emit(result)

    @visitor(dict)
    def visit_dict(self, d):
        old_result = self.result
        result = {}
        for k, v in d.items():
            self.result = None
            self.visit(v)
            result[k] = self.result
        self.result = old_result
        self.emit(result)


    def visit_generic(self, value):
        self.emit(value)

    def __call__(self, sh):
        self.visit(sh)
        return self.result


def render(sh):
    return RenderVisitor()(sh)
