from copy import deepcopy

from ..base import Term, Value, EvalEnv, TypeContext, QuoteContext, Callable

from .pi import PiValue
from .var import _QuoteVar


class LambdaValue(Callable):
    __slots__ = ["label", "domain", "fn"]

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
        # print(repr(body_val))
        return Lambda(
            label,
            self.domain.quote(ctx, normalize),
            body_val.quote(ctx.extend(label), normalize)
        )

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, LambdaValue):
            return False
        my_val = self(_QuoteVar("_", level))
        other_val = other(_QuoteVar("_", level))
        return my_val.alpha_equivalent(other_val, level + 1)

    def copy(self):
        # TODO: deepcopy needed ?
        return LambdaValue(self.label, self.domain.copy(), self.fn)


def memoize(fn):
    def wrapped(self, ctx=None):
        if ctx is not None:
            try:
                res = self._cache[ctx]
                print("Hit")
                return res
            except KeyError:
                print("Miss")
                pass
        result = fn(self, ctx)
        self._cache[ctx] = result
        return result
    return wrapped

class Lambda(Term):
    attrs = ["label", "type_", "body"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        self.type_.type(ctx)

        argtype = self.type_.eval()
        pi = PiValue(self.label, argtype)
        fresh = ctx.freshLocal(self.label)
        body = self.body.subst(self.label, fresh)
        bt = body.type(ctx.extend(self.label, argtype))

        def codomain(val):
            rebound = bt.quote().rebind(fresh)
            return rebound.eval(EvalEnv({self.label: [val]}))

        pi.codomain = codomain

        # typecheck the result
        pi.quote().type(ctx)

        return pi

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        domain = self.type_.eval(env)

        def fn(x: Value) -> Value:
            newenv = env.copy()
            newenv.insert(self.label, x)
            result = self.body.eval(newenv)
            # print(repr(result))
            return result

        return LambdaValue(self.label, domain, fn)

    def cbor_values(self):
        if self.label == "_":
            return [1, self.type_.cbor_values(), self.body.cbor_values()]
        return [1, self.label, self.type_.cbor_values(), self.body.cbor_values()]

    def subst(self, name, replacement, level=0):
        body_level = level + 1 if self.label == name else level
        return Lambda(
            self.label,
            self.type_.subst(name, replacement, level),
            self.body.subst(name, replacement, body_level))

    def rebind(self, local, level=0):
        body_level = level + 1 if self.label == local.name else level
        return Lambda(
            self.label,
            self.type_.rebind(local, level),
            self.body.rebind(local, body_level))

    def format_dhall(self):
        return (f"λ({self.label} : {self.type_.dhall()} ) →", self.body.format_dhall())

    def __str__(self):
        return f"λ({self.label} : {self.type_.dhall()} ) → {self.body}"



