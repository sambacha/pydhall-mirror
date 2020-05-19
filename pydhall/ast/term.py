from copy import deepcopy
from functools import reduce

import cbor

from .base import Node, Term
from . import value
from .type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class TypeContext(dict):
    def extend(self, name, value):
        ctx = self.__class__()
        for k, v in self:
            ctx[k] = list(v)
        ctx.setdefault(name, []).append(value)
        return ctx

    def freshLocal(self, name):
        return LocalVar(name=name, index=len(self.get(name, tuple())))


class EvalEnv(dict):
    def copy(self):
        return deepcopy(self)

    def insert(self, name, value):
        self.setdefault(name, []).insert(0, value)


class If(Term):
    attrs = ["cond", "true", "false"]
    _cbor_idx = 14

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        cond = self.cond.eval(env)
        if cond is value.True_:
            return self.true.eval()
        if cond is value.False_:
            return self.false.eval()

    def cbor_values(self):
        return [self.cond, self.true, self.false]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        cond = self.cond.type(ctx)
        if cond != value.Bool:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_PREDICATE)
        t = self.true.type()
        f = self.false.type()
        if t.quote().type() != value.Type or f.quote().type() != value.Type:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.IF_BRANCH_MUST_BE_TERM)
        if not t @ f:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.IF_BRANCH_MISMATCH)
        return t


class Lambda(Term):
    attrs = ["label", "type_", "body"]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        # typecheck the type
        self.type_.type(ctx)

        argtype = self.type_.eval()
        pi = value.Pi(self.label, argtype)
        fresh = ctx.freshLocal(self.label)
        body = self.body.subst(self.label, fresh)
        bt = body.type(ctx.extend(self.label, argtype))

        def codomain(val):
            rebound = bt.quote().rebind(fresh)
            return rebound.eval({self.label: [val]})

        pi.codomain = codomain

        # typecheck the result
        pi.quote().type(ctx)

        return pi

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        domain = self.type_.eval(env)

        def fn(x: value.Value) -> value.Value:
            newenv = env.copy()
            newenv.insert(self.label, x)
            return self.body.eval(newenv)

        return value._Lambda(self.label, domain, fn)

            
        # return lambda{
        #     Label:  t.Label,
        #     Domain: evalWith(t.Type, e),
        #     Fn: func(x Value) Value {
        #         newEnv := env{}
        #         for k, v := range e {
        #             newEnv[k] = v
        #         }
        #         newEnv[t.Label] = append([]Value{x}, newEnv[t.Label]...)
        #         return evalWith(t.Body, newEnv)
        #     },
        # }
        #
    def cbor_values(self):
        if self.label == "_":
            return [1, self.type_.cbor_values(), self.body.cbor_values()]
        return [1, self.label, self.type_.cbor_values(), self.body.cbor_values()]


class Pi(Term):
    attrs = ["label", "type_", "body"]

    def cbor_values(self):
        if self.label == "_":
            return [2, self.type_.cbor_values(), self.body.cbor_values()]
        return [2, self.label, self.type_, self.body]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        type_type = self.type_.type(ctx)
        if not isinstance(type_type, value.Universe):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_INPUT_TYPE)
        fresh = ctx.freshLocal(self.label)
        outUniv = self.body.subst(self.label, fresh).type(ctx.extend(self.label, self.type_.eval()))
        if not isinstance(type_type, value.Universe):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_OUPUT_TYPE)
        if outUniv is value.Type:
            return value.Type
        assert False

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        def codomain(x: value.Value) -> value.Value:
            newenv = env.copy()
            newenv.insert(self.label, x)
            return self.body.eval(newenv)
        return value.Pi(
            self.label,
            self.type_.eval(env),
            codomain)


class Annot(Term):
    attrs = ["expr", "annotation"]


class Var(Term):
    attrs = ["name", "index"]

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        max_idx = len(env.get(self.name, tuple()))
        if self.index >= max_idx:
            return value._FreeVar(self.name, self.index - max_idx)
        return env[self.name][self.index]

    def subst(self, name: str, replacement: "Term", level: int = 0):
        if self.name == name and self.index == level:
            return replacement
        return self

    def cbor_values(self):
        if self.name == "_":
            return self.index
        return [self.name, self.index]


class LocalVar(Term):
    attrs = ["name", "index"]

    def type(self, ctx=None):
        assert ctx is not None
        vals = ctx.get(self.name)
        assert vals is not None
        try:
            return vals[self.index]
        except IndexError:
            raise DhallTypeError(
                TYPE_ERROR_MESSAGE.UNBOUND_VARIABLE % self.name)


class _AtomicLit(Term):
    attrs = ["value"]


class NaturalLit(_AtomicLit):
    _type = value.Natural
    _cbor_idx = 15

    def eval(self, env=None):
        return value.NaturalLit(self.value)


class DoubleLit(_AtomicLit):
    _type = value.Double

    def eval(self, env=None):
        return value.DoubleLit(self.value)


class IntegerLit(_AtomicLit):
    _type = value.Integer
    _cbor_idx = 16

    def eval(self, env=None):
        return value.IntegerLit(self.value)


class BoolLit(_AtomicLit):
    _type = value.Bool

    def eval(self, env=None):
        return value.BoolLit(self.value)

    def cbor(self):
        return cbor.dumps(self.value)


class Chunk(Node):
    attrs = ["prefix", "expr"]


class TextLit(Term):
    attrs = ["chunks", "suffix"]


class Import(Term):
    attrs = ["import_hashed", "import_mode"]

    class Mode:
        Code = 0
        RawText = 1
        Location = 2


class Binding(Node):
    attrs = ["variable", "annotation", "value"]


class Let(Term):
    attrs = ["bindings", "body"]
    _cbor_idx = 25

    def eval(self, env=None):
        env = env.copy() if env is not None else EvalEnv()
        for b in self.bindings:
            env.insert(b.variable, b.value.eval(env))
        return self.body.eval(env)

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        let = self.copy()
        while len(let.bindings) > 0:
            binding = let.bindings.pop(0)
            binding_type = binding.value.type(ctx)
            if binding.annotation is not None:
                if not binding_type @ binding.annotation.eval():
                    raise DhallTypeError(
                        TYPE_ERROR_MESSAGE.ANNOT_MISMATCH % (
                            binding.annotation, binding_type.quote()))
            value = binding.value.eval().quote()
            let = let.subst(binding.variable, value)
            ctx = ctx.extend(binding.variable, binding_type)
        return let.body.type(ctx)

    def subst(self, name: str, replacement: "Term", level: int = 0):
        bindings = []
        for b in self.bindings:
            bindings.append(
                Binding(
                    b.variable,
                    b.annotation.subst(
                        name, replacement, level
                        ) if b.annotation is not None else None,
                    b.value.subst(name, replacement, level),
                )
            )
            if b.variable == name:
                level += 1
        return Let(bindings, self.body.subst(name, replacement, level))

    def cbor_values(self):
        bindings = reduce(
            lambda a, b: a + b,
            [[b.variable, b.annotation, b.value] for b in self.bindings])
        if isinstance(self.body, Let):
            return bindings + self.body.cbor_values()
        else:
            return bindings + [self.body]


class EmptyList(Term):
    attrs = ["type_"]


class Some(Term):
    attrs = ["val"]


class ToMap(Term):
    attrs = ["record", "type_"]


class Merge(Term):
    attrs = ["handler", "union", "annotation"]


class Op(Term):
    attrs = ["l", "r"]


class ImportAltOp(Op):
    precedence = 10
    operators = ("?",)


class OrOp(Op):
    precedence = 20
    operators = ("||",)


class PlusOp(Op):
    precedence = 30
    operators = ("+",)


class TextAppendOp(Op):
    precedence = 40
    operators = ("++",)


class ListAppendOp(Op):
    precedence = 50
    operators = ("#",)


class AndOp(Op):
    precedence = 60
    operators = ("&&",)


class RecordMergeOp(Op):
    precedence = 70
    operators = ("∧", "/\\")


class RightBiasedRecordMergeOp(Op):
    precedence = 80
    operators = ("⫽", "//")


class RecordTypeMergeOp(Op):
    precedence = 90
    operators = ("⩓", r"//\\")


class TimesOp(Op):
    precedence = 100
    operators = ("*",)


class EqOp(Op):
    precedence = 110
    operators = ("==",)


class NeOp(Op):
    precedence = 120
    operators = ("!=",)


class EquivOp(Op):
    precedence = 130
    operators = ("≡", "===")


class CompleteOp(Op):
    precedence = 140
    operators = ("::",)


class Universe(Term):
    def cbor(self):
        return cbor.dumps(self.__class__.__name__)

    @classmethod
    def from_name(cls, name):
        if name == "Type":
            return Type()
        if name == "Kind":
            return Kind()
        if name == "Sort":
            return Sort()
        assert False

    def cbor_values(self):
        return self.__class__.__name__

    def rebind(self, local, level=0):
        return self


class Sort(Universe):
    @property
    def type(self):
        raise DhallTypeError(TYPE_ERROR_MESSAGE.UNTYPED)


class Kind(Universe):
    _type = value.Sort


class Type(Universe):
    _type = value.Kind
    _eval = value.Type


class Builtin(Term):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__ = _builtin_cls[name]

    def __str__(self):
        return self.__class__.__name__

    def rebind(self, local, level=0):
        return self

    def cbor_values(self):
        return self.__class__.__name__.strip("_")


class _NaturalBuiltinMixin:
    def cbor_values(self):
        return self.__class__.__name__.replace("Natural", "Natural/")


class Double(Builtin):
    _type = value.Type


class Text(Builtin):
    _type = value.Type


class Bool(Builtin):
    _type = value.Type
    _eval = value.Bool

    def __init__(self):
        Term.__init__(self)


class Natural(Builtin):
    _type = value.Type


class Integer(Builtin):
    _type = value.Type


class List(Builtin):
    pass


class Optional(Builtin):
    pass


class None_(Builtin):
    pass


class NaturalBuild(_NaturalBuiltinMixin, Builtin):
    pass


class NaturalFold(_NaturalBuiltinMixin, Builtin):
    pass


class NaturalIsZero(_NaturalBuiltinMixin, Builtin):
    pass


class NaturalEven(_NaturalBuiltinMixin, Builtin):
    pass


class NaturalOdd(_NaturalBuiltinMixin, Builtin):
    pass


class NaturalToInteger(_NaturalBuiltinMixin, Builtin):
    pass


class NaturalShow(_NaturalBuiltinMixin, Builtin):
    pass


class NaturalSubtract(_NaturalBuiltinMixin, Builtin):
    pass


class IntegerClamp(Builtin):
    pass


class IntegerNegate(Builtin):
    pass


class IntegerToDouble(Builtin):
    pass


class IntegerShow(Builtin):
    pass


class DoubleShow(Builtin):
    pass


class TextShow(Builtin):
    pass


class ListBuild(Builtin):
    pass


class ListFold(Builtin):
    pass


class ListLength(Builtin):
    pass


class ListHead(Builtin):
    pass


class ListLast(Builtin):
    pass


class ListIndexed(Builtin):
    pass


class ListReverse(Builtin):
    pass


class OptionalBuild(Builtin):
    pass


class OptionalFold(Builtin):
    pass


_builtin_cls = {
    "Double": Double,
    "Text": Text,
    "Bool": Bool,
    "Natural": Natural,
    "Integer": Integer,
    "List": List,
    "Optional": Optional,
    "None": None_,
    "Natural/build": NaturalBuild,
    "Natural/fold": NaturalFold,
    "Natural/isZero": NaturalIsZero,
    "Natural/even": NaturalEven,
    "Natural/odd": NaturalOdd,
    "Natural/toInteger": NaturalToInteger,
    "Natural/show": NaturalShow,
    "Natural/subtract": NaturalSubtract,
    "Integer/clamp": IntegerClamp,
    "Integer/negate": IntegerNegate,
    "Integer/toDouble": IntegerToDouble,
    "Integer/show": IntegerShow,
    "Double/show": DoubleShow,
    "Text/show": TextShow,
    "List/build": ListBuild,
    "List/fold": ListFold,
    "List/length": ListLength,
    "List/head": ListHead,
    "List/last": ListLast,
    "List/indexed": ListIndexed,
    "List/reverse": ListReverse,
    "Optional/build": OptionalBuild,
    "Optional/fold": OptionalFold,
}

