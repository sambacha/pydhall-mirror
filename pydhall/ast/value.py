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
        raise NotImplementedError(f"{self.__class__.__name__}.alpha_equivalent")

    def __matmul__(self, other):
        return self.alpha_equivalent(other)

    def quote(self, ctx=None, normalize=False):
        raise NotImplementedError(f"{self.__class__.__name__}.quote")


class RecordLit(dict, Value):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import RecordLit
        for k, v in self.items():
            print(k)
            print(repr(v.quote(ctx, normalize)))
        return RecordLit({k: v.quote(ctx, normalize) for k, v in self.items()})


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


class BoolLit(Value):
    "Marker class for boolean literal"
    def __init__(self, val):
        self.__class__ = val and _True or _False

    def __eq__(self, other):
        return other.__class__ == self.__class__


class _False(BoolLit):
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


False_ = BoolLit(False)


class _True(BoolLit):
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


True_ = BoolLit(True)


class _IfVal(Value):
    def __init__(self, cond, true, false):
        self.cond = cond
        self.true = true
        self.false = false

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import If
        return If(
            self.cond.quote(ctx, normalize),
            self.true.quote(ctx, normalize),
            self.false.quote(ctx, normalize))


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

    def alpha_equivalent(self, other, level=0):
        return self == other


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

    def quote(self, ctx=None, normalize=False):
        from .term import IntegerLit
        return IntegerLit(int(self))

    def alpha_equivalent(self, other, level=0):
        return self == other


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

    def alpha_equivalent(self, other: "Value", level: int = 0) -> bool:
        return other.__class__ is _FreeVar and self.index == other.index and self.name == other.name


class _QuoteVar(Value):

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        assert ctx is not None
        from .term import Var
        return Var(self.name, ctx[self.name] - self.index - 1)

    def alpha_equivalent(self, other: "Value", level: int = 0) -> bool:
        return other.__class__ is _QuoteVar and self.index == other.index and self.name == other.name


class _LocalVar(Value):
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        from .term import LocalVar
        return LocalVar(self.name, self.index)

    def alpha_equivalent(self, other: "Value", level: int = 0) -> bool:
        return other.__class__ is _LocalVar and self.index == other.index and self.name == other.name


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
        # print(repr(body_val))
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
        res = Pi(
            label,
            self.domain.quote(ctx, normalize),
            body_val.quote(ctx.extend(label), normalize))
        # print(repr(res))
        return res


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
        print("-------------")
        print(repr(self.fn))
        print(repr(self.arg))
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


class Some(Value):
    def __init__(self, value: Value):
        self.value = value

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import Some
        return Some(self.value.quote(ctx, normalize=False))


class OptionalOf(Value):
    def __init__(self, type_):
        self.type_ = type_

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import App, Optional
        return App.build(Optional(), self.type_.quote(ctx, normalize))


class NoneOf(Value):
    def __init__(self, type_):
        self.type_ = type_


class _Op(Value):
    def __init__(self, l, r):
        self.l = l
        self.r = r


class _NeOp(_Op):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import NeOp
        return NeOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))

class _AndOp(_Op):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import AndOp
        return AndOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))


class _OptionalBuild(Callable):
    def __init__(self, type_=None):
        self.type_ = type_

    def __call__(self, x: Value) -> Value:
        if self.type_ == None:
            return _OptionalBuild(x)
        some = _Lambda("a", self.type_, lambda a: Some(a))
        return _App.build(x, OptionalOf(self.type_), some, NoneOf(self.type_))



OptionalBuild = _OptionalBuild()
