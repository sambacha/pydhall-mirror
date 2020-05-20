from copy import deepcopy
from functools import reduce

import cbor

from .base import Node, Term
from . import value
from .type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class TypeContext(dict):
    def extend(self, name, value):
        ctx = self.__class__()
        for k, v in self.items():
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
        # print(repr(self))
        # print(ctx)
        # print("--------------------------------------")
        # typecheck the type
        self.type_.type(ctx)

        argtype = self.type_.eval()
        pi = value.Pi(self.label, argtype)
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

        def fn(x: value.Value) -> value.Value:
            newenv = env.copy()
            newenv.insert(self.label, x)
            return self.body.eval(newenv)

        return value._Lambda(self.label, domain, fn)

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


class App(Term):
    attrs = ["fn", "arg"]

    @classmethod
    def build(cls, *args):
        assert args
        if len(args) == 1:
            return args[0]
        return App.build(App(args[0], args[1]), *args[2:])

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        fn_type = self.fn.type(ctx)
        arg_type = self.arg.type(ctx)
        if not isinstance(fn_type, value.Pi):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.NOT_A_FUNCTION)
        expected_type = fn_type.domain
        if not expected_type @ arg_type:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.TYPE_MISMATCH % (
                expected_type.quote(), arg_type.quote()))
        return fn_type.codomain(self.arg.eval())

    def subst(self, name: str, replacement: Term, level: int = 0):
        return App(
            self.fn.subst(name, replacement, level),
            self.arg.subst(name, replacement, level))

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return value._App.build(self.fn.eval(env), self.arg.eval(env))

    def cbor_values(self):
        return [0, self.fn.cbor_values(), self.arg.cbor_values()]

    def subst(self, name, replacement, level=0):
        return App(
            self.fn.subst(name, replacement, level),
            self.arg.subst(name, replacement, level))

    def rebind(self, local, level=0):
        return App(
            self.fn.rebind(local, level),
            self.arg.rebind(local, level))


class Annot(Term):
    attrs = ["expr", "annotation"]


class Var(Term):
    attrs = ["name", "index"]
    _cbor_idx = -4

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

    def type(self, ctx=None):
        raise DhallTypeError(
            TYPE_ERROR_MESSAGE.UNBOUND_VARIABLE % self.name)


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


class NonEmptyList(Term):
    attrs = ["content"]
    _cbor_idx = 4

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        t0 = self.content[0].type(ctx)
        t0.quote().assertType(value.Type, ctx, TYPE_ERROR_MESSAGE.INVALID_LIST_TYPE)
        for e in self.content[1:]:
            t1  = e.type(ctx)
            if not t0 @ t1:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISMATCH_LIST_ELEMENTS % ( t0.quote(), t1.quote()))

        return value.ListOf(t0)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return value.NonEmptyList([e.eval(env) for e in self.content])

    def cbor_values(self):
        return [4, None] + [e.cbor_values() for e in self.content]


class _AtomicLit(Term):
    attrs = ["value"]

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        if decoded is None:
            decoded = cbor.loads(encoded)
        return cls(decoded[1])

class NaturalLit(_AtomicLit):
    _type = value.Natural
    _cbor_idx = 15

    def eval(self, env=None):
        return value.NaturalLit(self.value)


class DoubleLit(_AtomicLit):
    _type = value.Double
    _cbor_idx = -3

    def eval(self, env=None):
        return value.DoubleLit(self.value)


class IntegerLit(_AtomicLit):
    _type = value.Integer
    _cbor_idx = 16

    def eval(self, env=None):
        return value.IntegerLit(self.value)


class BoolLit(_AtomicLit):
    _type = value.Bool
    _cbor_idx = -1

    def eval(self, env=None):
        return value.BoolLit(self.value)

    def cbor_values(self):
        return self.value


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

        # let := t
        let = self.copy()

        # for len(let.Bindings) > 0 {
        while len(let.bindings) > 0:
            # binding := let.Bindings[0]
            # let.Bindings = let.Bindings[1:]
            binding = let.bindings.pop(0)

            # bindingType, err := typeWith(ctx, binding.Value)
            # if err != nil {
            #     return nil, err
            # }
            binding_type = binding.value.type(ctx)

            # if binding.Annotation != nil {
            if binding.annotation is not None:
                # _, err := typeWith(ctx, binding.Value)
                # if err != nil {
                #     return nil, err
                # }
                # if !AlphaEquivalent(bindingType, Eval(binding.Annotation)) {
                #     return nil, mkTypeError(annotMismatch(binding.Annotation, Quote(bindingType)))
                # }
                binding.annotation.type(ctx)
                if not binding_type @ binding.annotation.eval():
                    raise DhallTypeError(
                        TYPE_ERROR_MESSAGE.ANNOT_MISMATCH % (
                            binding.annotation, binding_type.quote()))
            # }

            # value := Quote(Eval(binding.Value))
            # let = term.Subst(binding.Variable, value, let).(term.Let)
            # ctx = ctx.extend(binding.Variable, bindingType)
            value = binding.value.eval().quote()
            let = let.subst(binding.variable, value)
            ctx = ctx.extend(binding.variable, binding_type)
        # }
        # return typeWith(ctx, let.Body)
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
    _cbor_idx = 3

    _cbor_op_indexes = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        Op._cbor_indexes[cls._op_idx] = cls

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        if decoded is None:
            decoded = cbor.loads(encoded)
        return cls._cbor_op_indexes[decoded[1]](
            *[Term.from_cbor(i) for i in decoded[2:]])


class ImportAltOp(Op):
    precedence = 10
    operators = ("?",)
    _op_idx = 11


class OrOp(Op):
    precedence = 20
    operators = ("||",)
    _op_idx = 0


class PlusOp(Op):
    precedence = 30
    operators = ("+",)
    _op_idx = 4


class TextAppendOp(Op):
    precedence = 40
    operators = ("++",)
    _op_idx = 6


class ListAppendOp(Op):
    precedence = 50
    operators = ("#",)
    _op_idx = 7


class AndOp(Op):
    precedence = 60
    operators = ("&&",)
    _op_idx = 1


class RecordMergeOp(Op):
    precedence = 70
    operators = ("∧", "/\\")
    _op_idx = 8


class RightBiasedRecordMergeOp(Op):
    precedence = 80
    operators = ("⫽", "//")
    _op_idx = 9


class RecordTypeMergeOp(Op):
    precedence = 90
    operators = ("⩓", r"//\\")
    _op_idx = 10


class TimesOp(Op):
    precedence = 100
    operators = ("*",)
    _op_idx = 5


class EqOp(Op):
    precedence = 110
    operators = ("==",)
    _op_idx = 2


class NeOp(Op):
    precedence = 120
    operators = ("!=",)
    _op_idx = 3


class EquivOp(Op):
    precedence = 130
    operators = ("≡", "===")
    _op_idx = 12


class CompleteOp(Op):
    precedence = 140
    operators = ("::",)
    _op_idx = 13


class Builtin(Term):
    _cbor_idx = -2
    _by_name = {}
    _literal_name = None

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._literal_name is not None:
            key = cls._literal_name
        else:
            key = cls.__name__.strip("_")
        Builtin._by_name[key] = cls

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__ = Builtin._by_name[name]

    def __str__(self):
        return self.__class__.__name__

    def rebind(self, local, level=0):
        return self

    def cbor_values(self):
        return self.__class__.__name__.strip("_")


class Universe(Builtin):

    def __init__(self, *args, **kwargs):
        Term.__init__(self, *args, **kwargs)

    def cbor(self):
        return cbor.dumps(self.__class__.__name__)

    @classmethod
    def from_name(cls, name):
        return Builtin(name)

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
    _literal_name = "Natural/build"


class NaturalFold(_NaturalBuiltinMixin, Builtin):
    _literal_name = "Natural/fold"


class NaturalIsZero(_NaturalBuiltinMixin, Builtin):
    _literal_name = "Natural/isZero"


class NaturalEven(_NaturalBuiltinMixin, Builtin):
    _literal_name = "Natural/even"


class NaturalOdd(_NaturalBuiltinMixin, Builtin):
    _literal_name = "Natural/odd"


class NaturalToInteger(_NaturalBuiltinMixin, Builtin):
    _literal_name = "Natural/toInteger"


class NaturalShow(_NaturalBuiltinMixin, Builtin):
    _literal_name = "Natural/show"


class NaturalSubtract(_NaturalBuiltinMixin, Builtin):
    _literal_name = "Natural/substract"


class IntegerClamp(Builtin):
    _literal_name = "Integer/clamp"


class IntegerNegate(Builtin):
    _literal_name = "Integer/negate"


class IntegerToDouble(Builtin):
    _literal_name = "Integer/toDouble"


class IntegerShow(Builtin):
    _literal_name = "Integer/show"


class DoubleShow(Builtin):
    _literal_name = "Double/show"


class TextShow(Builtin):
    _literal_name = "Text/show"


class ListBuild(Builtin):
    _literal_name = "List/build"


class ListFold(Builtin):
    _literal_name = "List/fold"


class ListLength(Builtin):
    _literal_name = "List/length"


class ListHead(Builtin):
    _literal_name = "List/head"


class ListLast(Builtin):
    _literal_name = "List/last"


class ListIndexed(Builtin):
    _literal_name = "List/indexed"


class ListReverse(Builtin):
    _literal_name = "List/reverse"


class OptionalBuild(Builtin):
    _literal_name = "Optional/build"


class OptionalFold(Builtin):
    _literal_name = "Optional/fold"


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

