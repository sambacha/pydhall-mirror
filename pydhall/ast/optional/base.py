from ..base import Term, Builtin, Value, EvalEnv, Callable, QuoteContext, DependentValue, TypeContext
from ..universe import TypeValue
from pydhall.ast.type_error import TYPE_ERROR_MESSAGE
from ..function.pi import PiValue, FnType

## Optional
class _OptionalValue(Callable):
    def __call__(self, x: Value):
        return OptionalOf(x)

    def quote(self, ctx=None, normalize=None):
        return Optional()


OptionalValue = _OptionalValue()


class Optional(Builtin):
    _eval = OptionalValue

    def type(self, ctx=None):
        return FnType("_", TypeValue, TypeValue)


class OptionalOf(DependentValue):
    def __init__(self, type_):
        self.type_ = type_

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .. import App
        return App.build(Optional(), self.type_.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, OptionalOf):
            return False
        return self.type_.alpha_equivalent(other.type_)

    def copy(self):
        return OptionalOf(self.type_.copy())


## Some
class SomeValue(Value):
    def __init__(self, value: Value):
        self.value = value

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return Some(self.value.quote(ctx, normalize=False))

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        return self.value.alpha_equivalent(other.value, level)

    def copy(self):
        return SomeValue(self.value.copy())


class Some(Term):
    attrs = ["val"]

    def cbor_values(self):
        return [5, None, self.val.cbor_values()]

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return SomeValue(self.val.eval(env))

    def subst(self, name: str, replacement: Term, level: int =0):
        return Some(self.val.subst(name, replacement, level))

    def rebind(self, local: Term, level: int =0):
        return Some(self.val.rebind(local, level))

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        val_type = self.val.type(ctx)
        val_type.quote().assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.INVALID_SOME)
        return OptionalOf(val_type)


## None
class NoneOf(Value):
    def __init__(self, type_):
        self.type_ = type_

    def quote(self, ctx=None, normalize=None):
        ctx = ctx if ctx is not None else QuoteContext()
        from .. import App
        return App.build(None_(), self.type_.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        return self.type_.alpha_equivalent(other.type_, level)

    def copy(self):
        return NoneOf(self.type_.copy())


class _NoneValue(Callable):
    def __call__(self, x: Value):
        return NoneOf(x)

    def quote(self, ctx=None, normalize=None):
        return None_()


NoneValue = _NoneValue()


class None_(Builtin):
    _eval = NoneValue

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        return PiValue("A", TypeValue, lambda A: OptionalOf(A))


