from functools import reduce

import cbor

from .base import Node, Term
from . import value
from .type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class If(Term):
    attrs = ["cond", "true", "false"]
    _cbor_idx = 14

    def eval(self, env=None):
        env = env if env is not None else {}
        cond = self.cond.eval(env)
        if cond is value.True_:
            return self.true.eval()
        if cond is value.False_:
            return self.false.eval()

    def cbor_values(self):
        return [self.cond, self.true, self.false]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else {}
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


class Annot(Term):
    attrs = ["expr", "annotation"]


class Var(Term):
    attrs = ["name", "index"]

    def eval(self, env=None):
        env = env if env is not None else {}
        max_idx = len(env.get(self.name, tuple()))
        if self.index >= max_idx:
            return value._FreeVar(self.name, self.index - max_idx)
        return env[self.name][self.index]

    def subst(self, name: str, replacement: "Term", level: int):
        if self.name == name and self.index == level:
            return replacement
        return self

    def cbor(self):
        if self.name == "_":
            return cbor.dumps(self.index)
        return cbor.dumps([self.name, self.index])


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
        env = {} if env is None else dict(env)
        for b in self.bindings:
            env[b.variable] = [b.value.eval(env)] + list(env.get(b.variable, []))
        return self.body.eval(env)

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else {}
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
            ctx = dict(ctx)
            ctx.update({binding.variable: binding_type})
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


class Sort(Universe):
    @property
    def type(self):
        raise DhallTypeError(TYPE_ERROR_MESSAGE.UNTYPED)


class Kind(Universe):
    _type = value.Sort


class Type(Universe):
    _type = value.Kind


class Builtin(Term):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__ = _builtin_cls[name]

    def __str__(self):
        return self.__class__.__name__


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


class NaturalBuild(Builtin):
    pass


class NaturalFold(Builtin):
    pass


class NaturalIsZero(Builtin):
    pass


class NaturalEven(Builtin):
    pass


class NaturalOdd(Builtin):
    pass


class NaturalToInteger(Builtin):
    pass


class NaturalShow(Builtin):
    pass


class NaturalSubtract(Builtin):
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

