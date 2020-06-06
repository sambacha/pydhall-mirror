from ..base import Term, Value, EvalEnv, TypeContext, QuoteContext
from ..universe import UniverseValue, TypeValue

from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from .var import _QuoteVar


class PiValue(Value):
    def __init__(self, label, domain, codomain=None):
        self.label = label
        self.domain = domain
        self.codomain = codomain

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()

        label = "_" if normalize else self.label
        body_val = self.codomain(_QuoteVar(label, ctx.get(label, 0)))
        res = Pi(
            label,
            self.domain.quote(ctx, normalize),
            body_val.quote(ctx.extend(label), normalize))
        # print(repr(res))
        return res

    def __str__(self):
        return f"PiValue({repr(self.label)}, {str(self.domain)}, {str(self.codomain)})"

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, PiValue):
            return False
        my_codomain = self.codomain(_QuoteVar("_", level))
        other_codomain = self.codomain(_QuoteVar("_", level))
        return my_codomain.alpha_equivalent(other_codomain, level + 1)
        # v2, ok := v2.(Pi)
        # if !ok {
        #     return false
        # }
        # return alphaEquivalentWith(level, v1.Domain, v2.Domain) &&
        #     alphaEquivalentWith(
        #         level+1,
        #         v1.Codomain(quoteVar{Name: "_", Index: level}),
        #         v2.Codomain(quoteVar{Name: "_", Index: level}),
        #     )


def FnType(label: str, domain: Value, codomain: Value) -> PiValue:
    "Create a non-dependent function type value"
    return PiValue(label, domain, lambda x: codomain)


class Pi(Term):
    attrs = ["label", "type_", "body"]

    def cbor_values(self):
        if self.label == "_":
            return [2, self.type_.cbor_values(), self.body.cbor_values()]
        return [2, self.label, self.type_.cbor_values(), self.body.cbor_values()]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        # inUniv, err := typeWith(ctx, t.Type)
        # if err != nil {
        #     return nil, err
        # }
        type_type = self.type_.type(ctx)

        # i, ok := inUniv.(Universe)
        # if !ok {
        #     return nil, mkTypeError(invalidInputType)
        # }
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
        # outUniv, err := typeWith(
        #     ctx.extend(t.Label, Eval(t.Type)),
        #     term.Subst(t.Label, freshLocal, t.Body))
        # if err != nil {
        #     return nil, err
        # }
        # o, ok := outUniv.(Universe)
        # if !ok {
        #     return nil, mkTypeError(invalidOutputType)
        # }
        # return functionCheck(i, o), nil

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
