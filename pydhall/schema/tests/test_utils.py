from pydhall.schema.utils import SchemaVisitor, visitor
from pydhall.schema import *

def test_visitor_class():

    class Sub2(Record):
        n = NaturalField()

    class Sub1(Record):
        s = RecordField(Sub2)

    class Conf(Record):
        s = RecordField(Sub1)
        s2 = RecordField(Sub2)

    class Vis(SchemaVisitor):
        def __init__(self):
            self.found = []
            self.prefix = ""

        @visitor(Record)
        def visit_record(self, r):
            self.found.append(self.prefix + r.__name__)
            old_prefix = self.prefix
            self.prefix += "%s_" % r.__name__
            for f in r._pydhall_fields:
                self.visit(f)
            self.prefix = old_prefix

    v = Vis()
    v.visit(Conf)
    assert v.found == ["Conf", "Conf_Sub1", "Conf_Sub1_Sub2", "Conf_Sub2"]
