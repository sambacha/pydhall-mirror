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


class OptionalFold(Builtin):
    _literal_name = "Optional/fold"
    _type = "∀(a : Type) → Optional a → ∀(optional : Type) → ∀(just : a → optional) → ∀(nothing : optional) → optional"

    def __call__(self, typ1, opt, typ2, some, x) -> Value:
        if isinstance(opt, SomeValue):
            return some(opt.value)
        if isinstance(opt, NoneOf):
            return x
        return None
