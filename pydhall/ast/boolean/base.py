from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from ..base import _AtomicLit, BuiltinValue, Value, Term, Builtin, EvalEnv, Value, QuoteContext, TypeContext
from ..universe import TypeValue

BoolTypeValue = BuiltinValue("Bool")


class Bool(Builtin):
    _type = TypeValue
    _eval = BoolTypeValue

    def __init__(self):
        Term.__init__(self)

    def __hash__(self):
        return hash(self.__class__)


class BoolLit(_AtomicLit):
    _type = BoolTypeValue
    _cbor_idx = -1

    def eval(self, env=None):
        return BoolLitValue(self.value)

    def cbor_values(self):
        return self.value


class BoolLitValue(Value):
    "Marker class for boolean literal"
    def __init__(self, val):
        self.__class__ = val and _True or _False

    def __eq__(self, other):
        return other.__class__ == self.__class__

    def alpha_equivalent(self, other, level=0):
        return other == self

    def copy(self):
        return self


class _False(BoolLitValue):
    type = BoolTypeValue

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
        return BoolLit(False)


False_ = BoolLitValue(False)


class _True(BoolLitValue):
    type = BoolTypeValue

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
        return BoolLit(True)


True_ = BoolLitValue(True)


class IfValue(Value):
    def __init__(self, cond, true, false):
        self.cond = cond
        self.true = true
        self.false = false

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return If(
            self.cond.quote(ctx, normalize),
            self.true.quote(ctx, normalize),
            self.false.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.cond.alpha_equivalent(other.cond, level)
            and self.true.alpha_equivalent(other.true, level)
            and self.false.alpha_equivalent(other.false, level))

    def copy(self):
        return IfValue(self.cond.copy(), self.true.copy(), self.false.copy())


class If(Term):
    # attrs = ['cond', 'true', 'false']
    __slots__ = ['cond', 'true', 'false']

    def __init__(self, cond, true, false, **kwargs):
        self.cond = cond
        self.true = true
        self.false = false

    def copy(self, **kwargs):
        new = If(
            self.cond,
            self.true,
            self.false
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    _rebindable = ["cond", "true", "false"]
    _cbor_idx = 14

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        cond = self.cond.eval(env)
        # print(repr(cond))
        if cond == True_:
            return self.true.eval(env)
        elif cond == False_:
            return self.false.eval(env)
        t = self.true.eval(env)
        f = self.false.eval(env)
        if t == True_ and f == False_:
            return cond
        if t @ f:
            return t
        return IfValue(cond, t, f)

    def cbor_values(self):
        return [14, self.cond.cbor_values(), self.true.cbor_values(), self.false.cbor_values()]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        cond = self.cond.type(ctx)
        if cond != BoolTypeValue:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_PREDICATE)
        t = self.true.type(ctx)
        f = self.false.type(ctx)
        if t.quote().type(ctx) != TypeValue or f.quote().type(ctx) != TypeValue:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.IF_BRANCH_MUST_BE_TERM)
        if not t @ f:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.IF_BRANCH_MISMATCH)
        return t

    def subst(self, name, replacement, level=0):
        return If(
            self.cond.subst(name, replacement, level),
            self.true.subst(name, replacement, level),
            self.false.subst(name, replacement, level),
        )

    def format_dhall(self):
        return (("if", self.cond.format_dhall()), ("then", self.true.format_dhall()), ("else", self.false.format_dhall()))
