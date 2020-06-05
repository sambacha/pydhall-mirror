from ..base import _AtomicLit, BuiltinValue, Value, Term, Builtin
from ..universe import TypeValue

BoolTypeValue = BuiltinValue("Bool")


class Bool(Builtin):
    _type = TypeValue
    _eval = BoolTypeValue

    def __init__(self):
        Term.__init__(self)


class BoolLit(_AtomicLit):
    _type = BoolTypeValue
    _cbor_idx = -1

    def eval(self, env=None):
        return BoolLitValue(self.value)

    def cbor_values(self):
        return self.value


class BoolLitValue(Value):
    "Marker class for boolean literal"
    def __init__(self, val):
        self.__class__ = val and _True or _False

    def __eq__(self, other):
        return other.__class__ == self.__class__


class _False(BoolLitValue):
    type = BoolTypeValue

    def as_python(self):
        return False

    def as_dhall(self):
        return "False"

    def __repr__(self):
        return "False"

    def __str__(self):
        return "False"

    def __bool__(self):
        return False

    def quote(self, ctx=None, normalize=False):
        return BoolLit(False)


False_ = BoolLitValue(False)


class _True(BoolLitValue):
    type = BoolTypeValue

    def as_python(self):
        return True

    def as_dhall(self):
        return "True"

    def __repr__(self):
        return "True"

    def __str__(self):
        return "True"

    def __bool__(self):
        return True

    def quote(self, ctx=None, normalize=False):
        return BoolLit(True)


True_ = BoolLitValue(True)
