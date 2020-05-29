from .base import Term, Builtin, Value, EvalEnv, Callable, QuoteContext, DependentValue, TypeContext
from .universe import TypeValue
from ..type_error import TYPE_ERROR_MESSAGE

## Optional
class _OptionalValue(Callable):
    def __call__(self, x: Value):
        return OptionalOf(x)


OptionalValue = _OptionalValue()


class Optional(Builtin):
    _eval = OptionalValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType
        return FnType("_", TypeValue, TypeValue)


class OptionalOf(DependentValue):
    def __init__(self, type_):
        self.type_ = type_

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from . import App
        return App.build(Optional(), self.type_.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, OptionalOf):
            return False
        return self.type_.alpha_equivalent(other.type_)



## Some
class SomeValue(Value):
    def __init__(self, value: Value):
        self.value = value

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return Some(self.value.quote(ctx, normalize=False))


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
        return Some(self.subst.rebind(local, level))

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
        from . import App
        return App.build(None_(), self.type_.quote(ctx, normalize))


class _NoneValue(Callable):
    def __call__(self, x: Value):
        return NoneOf(x)


NoneValue = _NoneValue()


class None_(Builtin):
    _eval = NoneValue

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        from pydhall.ast.value import Pi
        return Pi("A", TypeValue, lambda A: OptionalOf(A))


## Funtions
class _OptionalBuildValue(Callable):
    def __init__(self, type_=None):
        self.type_ = type_

    def __call__(self, x: Value) -> Value:
        if self.type_ == None:
            return _OptionalBuildValue(x)
        from pydhall.ast.value import _Lambda, _App
        some = _Lambda("a", self.type_, lambda a: SomeValue(a))
        return _App.build(x, OptionalOf(self.type_), some, NoneOf(self.type_))


OptionalBuildValue = _OptionalBuildValue()


class OptionalBuild(Builtin):
    _literal_name = "Optional/build"
    _eval = OptionalBuildValue

    def type(self, ctx=None):
        # TODO: understand and document this.
        ctx = ctx if ctx is not None else TypeContext()
        from pydhall.ast.value import Pi, FnType
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType(
                "_",
                Pi(
                    "optional",
                    TypeValue,
                    lambda optional: FnType(
                        "just",
                        FnType("_", a, optional),
                        FnType("nothing", optional, optional)
                    )
                ),
                OptionalOf(a)
            )
        )


class _OptionalFoldValue(Callable):
    def __init__(self, typ1=None, opt=None, typ2=None, some=None):
        self.typ1 = typ1
        self.opt = opt
        self.typ2 = typ2
        self.some = some

    def __call__(self, x: Value) -> Value:
        if self.typ1 is None:
            return _OptionalFoldValue(x)
        if self.opt is None:
            return _OptionalFoldValue(self.typ1, x)
        if self.typ2 is None:
            return _OptionalFoldValue(self.typ1, self.opt, x)
        if self.some is None:
            return _OptionalFoldValue(self.typ1, self.opt, self.typ2, x)
        if isinstance(self.opt, SomeValue):
            return self.some(self.opt.value)
        if isinstance(self.opt, NoneOf):
            return x
        return None

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        result = OptionalFold()
        from . import App
        for arg in ["typ1", "opt", "typ2", "some"]:
            nextarg = getattr(self, arg)
            if nextarg is None:
                return result
            result = App(result, nextarg.quote(ctx, normalize))
        return result


OptionalFoldValue = _OptionalFoldValue()

class OptionalFold(Builtin):
    _literal_name = "Optional/fold"
    _eval = OptionalFoldValue

    def type(self, ctx=None):
        # TODO: understand and document this.
        ctx = ctx if ctx is not None else TypeContext()
        from pydhall.ast.value import Pi, FnType
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType(
                "_",
                OptionalOf(a),
                Pi(
                    "optional",
                    TypeValue,
                    lambda optional: FnType(
                        "just",
                        FnType("_", a, optional),
                        FnType("nothing", optional, optional)
                    )
                )
            )
        )
