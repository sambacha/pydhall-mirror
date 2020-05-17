class Value:
    def __str__(self):
        return str(self.as_python())

    @classmethod
    def from_python(cls, value):
        cls(value)

    def alpha_equivalent(self, other: "Value", level: int = 0) -> bool:
        raise NotImplementedError(f"{self.__class__.name}.alpha_equivalent")

    def __matmul__(self, other):
        return self.alpha_equivalent(other)


class Universe(Value):
    def __init__(self, name, type):
        self.name = name
        self._type = type

    def __repr__(self):
        return f"Universe({self.name})"

    def __str__(self):
        self.name

    def alpha_equivalent(self, other, level=0):
        return other is self


Sort = Universe("Sort", None)
Kind = Universe("Kind", Sort)
Type = Universe("Type", Kind)


class Builtin(Value):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Builtin({self.name})"

    def __str__(self):
        self.name

    def quote(self, ctx=None, normalize=False):
        # ctx = ctx if ctx is not None else {}
        from .term import Builtin
        return Builtin(self.name)

    def alpha_equivalent(self, other, level=0):
        return other is self


Double = Builtin("Double")
Text = Builtin("Text")
Bool = Builtin("Bool")
Natural = Builtin("Natural")
Integer = Builtin("Integer")


class _False(Value):
    type = Bool

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
        from .term import BoolLit
        return BoolLit(False)


False_ = _False()


class _True(Value):
    type = Bool

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
        from .term import BoolLit
        return BoolLit(True)


True_ = _True()


def BoolLit(val):
    if val:
        return True_
    else:
        return False_


class NaturalLit(int, Value):

    def __new__(cls, val):
        if val < 0:
            raise ValueError("%s < 0" % val)
        return int.__new__(cls, val)

    def __add__(self, other):
        if not isinstance(other, NaturalLit):
            raise ValueError(other)
        return NaturalLit(int.__add__(self, other))

    def as_python(self):
        return int(self)

    def as_dhall(self):
        return str(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({int.__repr__(self)})"

    def quote(self, ctx=None, normalize=False):
        from .term import NaturalLit
        return NaturalLit(int(self))


class IntegerLit(int, Value):

    def __add__(self, other):
        raise TypeError()

    def as_python(self):
        return int(self)

    def as_dhall(self):
        sign = "+" if self >= 0 else "-"
        return f"{sign}{str(self)}"

    def __repr__(self):
        return f"{self.__class__.__name__}({int.__repr__(self)})"


class DoubleLit(float, Value):

    def __add__(self, other):
        raise TypeError()

    def as_python(self):
        return float(self)

    def as_dhall(self):
        return str(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({float.__repr__(self)})"


class _FreeVar(Value):
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        from .term import Var
        return Var(self.name, self.index)
