class QuoteContext(dict):
    def extend(self, name):
        new = QuoteContext(self)
        new[name] = self.get(name, 0) + 1
        return new

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

    def quote(self, ctx=None, normalize=False):
        raise NotImplementedError(f"{self.__class__.__name__}.quote")


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

    def quote(self, ctx=None, normalize=False):
        from .term import Universe
        return Universe.from_name(self.name)


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


class _QuoteVar(Value):

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        assert ctx is not None
        from .term import Var
        return Var(self.name, ctx[self.name] - self.index - 1)


class Callable(Value):
    def __call__(self, arg):
        raise NotImplementedError()


class _Lambda(Callable):
    def __init__(self, label, domain, fn):
        self.label = label
        self.domain = domain
        self.fn = fn

    def __call__(self, x: Value) -> Value:
        return self.fn(x)

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        label = "_" if normalize else self.label
        body_val = self(_QuoteVar(label, ctx.get(label, 0)))
        from .term import Lambda
        return Lambda(
            label,
            self.domain.quote(ctx, normalize),
            body_val.quote(ctx.extend(label), normalize)
        )

class Pi(Value):
    def __init__(self, label, domain, codomain=None):
        self.label = label
        self.domain = domain
        self.codomain = codomain

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()

        label = "_" if normalize else self.label
        body_val = self.codomain(_QuoteVar(label, ctx.get(label, 0)))
        from .term import Pi
        return Pi(
            label,
            self.domain.quote(ctx, normalize),
            body_val.quote(ctx.extend(label), normalize))


class _App(Value):
    def __init__(self, fn, arg):
        self.fn = fn
        self.arg = arg

    @classmethod
    def build(cls, *args):
        assert args
        if len(args) == 1:
            return args[0]
        if isinstance(args[0], Callable):
            result = args[0](args[1])
        else:
            result = _App(args[0], args[1])

        return _App.build(result, *args[2:])

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import App
        return App(
            self.fn.quote(ctx, normalize),
            self.arg.quote(ctx, normalize))


class ListOf(Value):
    def __init__(self, type_):
        self.type_ = type_


class NonEmptyList(Value):
    def __init__(self, content):
        self.content = content

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import NonEmptyList
        return NonEmptyList([e.quote(ctx, normalize) for e in self.content])
