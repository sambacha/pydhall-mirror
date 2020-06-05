from .term.base import Value, BuiltinValue, QuoteContext, Callable, OpValue

Text = BuiltinValue("Text")
Bool = BuiltinValue("Bool")


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

    def __str__(self):
        return f"Pi({repr(self.label)}, {str(self.domain)}, {str(self.codomain)})"

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, Pi):
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


def FnType(label: str, domain: Value, codomain: Value) -> Pi:
    "Create a non-dependent function type value"
    return Pi(label, domain, lambda x: codomain)


class _App(Value):
    def __init__(self, fn, arg):
        self.fn = fn
        self.arg = arg

    @classmethod
    def build(cls, *args):
        assert args
        # print("***********")
        # print(args)
        if len(args) == 1:
            return args[0]
        # if args[1] == 13.37:
        #     import ipdb; ipdb.set_trace()
        if isinstance(args[0], Callable):
            # try to apply the function
            result = args[0](args[1])
            if result is None:
                # print("None")
                result = _App(args[0], args[1])
        else:
            result = _App(args[0], args[1])

        return _App.build(result, *args[2:])

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import App
        # print("-------------")
        # print(repr(self.fn))
        # print(repr(self.arg))
        return App(
            self.fn.quote(ctx, normalize),
            self.arg.quote(ctx, normalize))


class _NeOp(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import NeOp
        return NeOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))

class _AndOp(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import AndOp
        return AndOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))

class _OrOp(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import OrOp
        return OrOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))
