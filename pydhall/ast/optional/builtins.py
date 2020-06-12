from ..base import Term, Builtin, Value, EvalEnv, Callable, QuoteContext, DependentValue, TypeContext
from ..universe import TypeValue
from pydhall.ast.type_error import TYPE_ERROR_MESSAGE
from ..function.pi import PiValue, FnType
from ..function.lambda_ import LambdaValue
from ..function.app import AppValue

from .base import OptionalOf, NoneOf, SomeValue


class OptionalBuild(Builtin):
    _literal_name = "Optional/build"
    _type = "∀(a : Type) → (∀(optional : Type) → ∀(just : a → optional) → ∀(nothing : optional) → optional) → Optional a"

    def __call__(self, type_, x) -> Value:
        some = LambdaValue("a", type_, lambda a: SomeValue(a))
        return AppValue.build(x, OptionalOf(type_), some, NoneOf(type_))



class _OptionalFoldValue(Callable):
    def __init__(self, typ1=None, opt=None, typ2=None, some=None):
        self.typ1 = typ1
        self.opt = opt
        self.typ2 = typ2
        self.some = some


    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        result = OptionalFold()
        from .. import App
        for arg in ["typ1", "opt", "typ2", "some"]:
            nextarg = getattr(self, arg)
            if nextarg is None:
                return result
            result = App(result, nextarg.quote(ctx, normalize))
        return result


OptionalFoldValue = _OptionalFoldValue()

class OptionalFold(Builtin):
    _literal_name = "Optional/fold"
    _type = "∀(a : Type) → Optional a → ∀(optional : Type) → ∀(just : a → optional) → ∀(nothing : optional) → optional"

    def __call__(self, typ1, opt, typ2, some, x) -> Value:
        if isinstance(opt, SomeValue):
            return some(opt.value)
        if isinstance(opt, NoneOf):
            return x
        return None

    def oldtype(self, ctx=None):
        # TODO: understand and document this.
        ctx = ctx if ctx is not None else TypeContext()
        return PiValue(
            "a",
            TypeValue,
            lambda a: FnType(
                "_",
                OptionalOf(a),
                PiValue(
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
