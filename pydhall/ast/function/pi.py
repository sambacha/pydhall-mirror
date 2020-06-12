from ..base import Term, Value, EvalEnv, TypeContext, QuoteContext
from ..universe import UniverseValue, TypeValue

from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from .var import _QuoteVar


_cache = {}

class PiValue(Value):
    def __init__(self, label, domain, codomain=None):
        self.label = label
        self.domain = domain
        self.codomain = codomain

    def quote(self, ctx=None, normalize=False):

        ctx = ctx if ctx is not None else QuoteContext()
        label = "_" if normalize else self.label
        # if not ctx:
        #     try:
        #         res = _cache[(label, self.domain, self.codomain)]
        #         # print("Hit")
        #         return res
        #     except KeyError:
        #         pass
        # print("Miss")
        body_val = self.codomain(_QuoteVar(label, ctx.get(label, 0)))
        res = Pi(
            label,
            self.domain.quote(ctx, normalize),
            body_val.quote(ctx.extend(label), normalize))
        # if not ctx:
        #     _cache[(label, self.domain, self.codomain)] = res
        return res

    def __str__(self):
        return f"PiValue({repr(self.label)}, {str(self.domain)}, {str(self.codomain)})"

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, PiValue):
            return False
        if not self.domain.alpha_equivalent(other.domain, level):
            return False
        my_codomain = self.codomain(_QuoteVar("_", level))
        other_codomain = other.codomain(_QuoteVar("_", level))
        return my_codomain.alpha_equivalent(other_codomain, level + 1)

    def copy(self):
        return PiValue(self.label, self.domain.copy(), self.codomain)


def FnType(label: str, domain: Value, codomain: Value) -> PiValue:
    "Create a non-dependent function type value"
    return PiValue(label, domain, lambda x: codomain)


class Pi(Term):
    # attrs = ['label', 'type_', 'body']
    __slots__ = ['label', 'type_', 'body']

    def __init__(self, label, type_, body, **kwargs):
        self.label = label
        self.type_ = type_
        self.body = body

    def copy(self, **kwargs):
        new = Pi(
            self.label,
            self.type_,
            self.body
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new


    def cbor_values(self):
        if self.label == "_":
            return [2, self.type_.cbor_values(), self.body.cbor_values()]
        return [2, self.label, self.type_.cbor_values(), self.body.cbor_values()]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        type_type = self.type_.type(ctx)

        if not isinstance(type_type, UniverseValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_INPUT_TYPE)

        # freshLocal := ctx.freshLocal(t.Label)
        fresh = ctx.freshLocal(self.label)
        outUniv = self.body.subst(self.label, fresh).type(ctx.extend(self.label, self.type_.eval()))
        if not isinstance(outUniv, UniverseValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_OUTPUT_TYPE)
        if outUniv is TypeValue:
            return TypeValue
        if type_type < outUniv:
            return outUniv
        return type_type

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        def codomain(x: Value) -> Value:
            newenv = env.copy()
            newenv.insert(self.label, x)
            return self.body.eval(newenv)
        return PiValue(
            self.label,
            self.type_.eval(env),
            codomain)

    def subst(self, name, replacement, level=0):
        body_level = level + 1 if self.label == name else level
        return Pi(
            self.label,
            self.type_.subst(name, replacement, level),
            self.body.subst(name, replacement, body_level))

    def rebind(self, local, level=0):
        body_level = level + 1 if self.label == local.name else level
        return Pi(
            self.label,
            self.type_.rebind(local, level),
            self.body.rebind(local, body_level))

    def __str__(self):
        return f"∀ ( {self.label} : {self.type_} ) → {self.body}"

