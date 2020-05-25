from copy import deepcopy
from functools import reduce

import cbor

from ..base import Node, Term
from .. import value
from ..type_error import DhallTypeError, TYPE_ERROR_MESSAGE


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


class RecordLit(dict, Term):
    def __init__(self, fields, *args, **kwargs):
        Term.__init__(self, *args, **kwargs)
        dict.__init__(self, fields)

    def cbor_values(self):
        return [8, {k: self[k].cbor_values() for k in sorted(list(self.keys()))}]

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return value.RecordLit({k: v.eval(env) for k, v in self.items()})


class RecordType(dict, Term):
    def __init__(self, fields, *args, **kwargs):
        Term.__init__(self, *args, **kwargs)
        dict.__init__(self, fields)

    def cbor_values(self):
        return [7, {k: self[k].cbor_values() for k in sorted(list(self.keys()))}]


class If(Term):
    attrs = ["cond", "true", "false"]
    _rebindable = ["cond", "true", "false"]
    _cbor_idx = 14

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        cond = self.cond.eval(env)
        # print(repr(cond))
        if cond == value.True_:
            return self.true.eval(env)
        elif cond == value.False_:
            return self.false.eval(env)
        t = self.true.eval(env)
        f = self.false.eval(env)
        if t == value.True_ and f == value.False_:
            return cond
        if t @ f:
            return t
        return value._IfVal(cond, t, f)

    def cbor_values(self):
        return [14, self.cond.cbor_values(), self.true.cbor_values(), self.false.cbor_values()]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        cond = self.cond.type(ctx)
        if cond != value.Bool:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_PREDICATE)
        t = self.true.type(ctx)
        f = self.false.type(ctx)
        if t.quote().type(ctx) != value.Type or f.quote().type(ctx) != value.Type:
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
        # print(ctx.extend(self.label, argtype))
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
            result = self.body.eval(newenv)
            # print(repr(result))
            return result

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

    def format_dhall(self):
        return (f"λ({self.label} : {self.type_.dhall()} ) →", self.body.format_dhall())


class Pi(Term):
    attrs = ["label", "type_", "body"]

    def cbor_values(self):
        if self.label == "_":
            return [2, self.type_.cbor_values(), self.body.cbor_values()]
        return [2, self.label, self.type_.cbor_values(), self.body.cbor_values()]

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
        print(repr(self.fn))
        print(repr(self.arg))
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

    def cbor_values(self):
        return [26, self.expr.cbor_values(), self.annotation.cbor_values()]


class Var(Term):
    attrs = ["name", "index"]
    _rebindable = []
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

    def format_dhall(self):
        index = "" if not self.index else f"@{self.index}"
        return (f"{self.name}{index}",)


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

    def eval(self, env=None):
        return value._LocalVar(self.name, self.index)

    def rebind(self, local, level=0):
        if local.name == self.name and local.index == self.index:
            return Var(self.name, level)
        return self


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

    def format_dhall(self):
        return (str(self.value),)

class NaturalLit(_AtomicLit):
    _type = value.Natural
    _cbor_idx = 15

    def eval(self, env=None):
        return value.NaturalLit(self.value)


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

    def cbor_values(self):
        out = [18]
        for c in self.chunks:
            out.append(c.prefix, c.expr.cbor_values())
        out.append(self.suffix)
        return out


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
                binding.annotation.type(ctx)
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
            [[b.variable, b.annotation.cbor_values(), b.value.cbor_values()] for b in self.bindings])
        if isinstance(self.body, Let):
            return [25] + bindings + self.body.cbor_values()
        else:
            return [25] + bindings + [self.body.cbor_values()]


class EmptyList(Term):
    attrs = ["type_"]


class Some(Term):
    attrs = ["val"]

    def cbor_values(self):
        return [5, None, self.val.cbor_values()]


class ToMap(Term):
    attrs = ["record", "type_"]


class Merge(Term):
    attrs = ["handler", "union", "annotation"]


class Op(Term):
    attrs = ["l", "r"]
    _rebindable = ["l", "r"]
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

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        self.r.assertType(self._type, ctx, TYPE_ERROR_MESSAGE.CANT_OP % (self.operators[0], self._type.__class__.__name__))
        self.l.assertType(self._type, ctx, TYPE_ERROR_MESSAGE.CANT_OP % (self.operators[0], self._type.__class__.__name__))
        return self._type

    def cbor_values(self):
        return [3, self._op_idx, self.l.cbor_values(), self.r.cbor_values()]

    def subst(self, name: str, replacement: "Term", level: int = 0):
        return self.__class__(
            self.l.subst(name, replacement, level),
            self.r.subst(name, replacement, level),
        )


class ImportAltOp(Op):
    precedence = 10
    operators = ("?",)
    _op_idx = 11


class OrOp(Op):
    precedence = 20
    operators = ("||",)
    _op_idx = 0
    _type = value.Bool


class PlusOp(Op):
    precedence = 30
    operators = ("+",)
    _op_idx = 4
    _type = value.Natural

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, value.NaturalLit):
            if isinstance(r, value.NaturalLit):
                return value.NaturalLit(l + r)
            if l == 0:
                return r
        if isinstance(r, value.NaturalLit):
            if r == 0:
                return l
        return value._PlusOp(l,r)


class TextAppendOp(Op):
    precedence = 40
    operators = ("++",)
    _op_idx = 6
    _type = value.Text


class ListAppendOp(Op):
    precedence = 50
    operators = ("#",)
    _op_idx = 7


class AndOp(Op):
    precedence = 60
    operators = ("&&",)
    _op_idx = 1
    _type = value.Bool

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, value.BoolLit):
            if l:
                return r
            return False
        if isinstance(r, value.BoolLit):
            if r:
                return l
            return False
        if l @ r:
            return l
        return value._AndOp(l,r)

    def format_dhall(self):
        return (self.l.format_dhall(), "&&", self.r.format_dhall())


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
    _type = value.Natural


class EqOp(Op):
    precedence = 110
    operators = ("==",)
    _op_idx = 2
    _type = value.Bool

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, value.BoolLit) and l:
            return r
        if isinstance(r, value.BoolLit) and r:
            return l
        if l @ r:
            return BoolLit(True)
        return value._EqOp(l,r)


class NeOp(Op):
    precedence = 120
    operators = ("!=",)
    _op_idx = 3
    _type = value.Bool

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, value.BoolLit) and not l:
            return r
        if isinstance(r, value.BoolLit) and not r:
            return l
        if l @ r:
            return BoolLit(False)
        return value._NeOp(l,r)


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

    def __init__(self, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if name is not None:
            self.__class__ = Builtin._by_name[name]

    def __str__(self):
        return self.__class__.__name__

    def rebind(self, local, level=0):
        return self

    def cbor_values(self):
        if self._literal_name is not None:
            return self._literal_name
        else:
            return self.__class__.__name__.strip("_")

    def format_dhall(self):
        name = self._literal_name if self._literal_name is not None else self.__class__.__name__.strip("_")
        return (name,)


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
    pass


class Double(Builtin):
    _type = value.Type
    _eval = value.Double


class Text(Builtin):
    _type = value.Type
    _eval = value.Text


class Bool(Builtin):
    _type = value.Type
    _eval = value.Bool

    def __init__(self):
        Term.__init__(self)


class Natural(Builtin):
    _type = value.Type
    _eval = value.Natural


class Integer(Builtin):
    _type = value.Type
    _eval = value.Integer


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
    _eval = value.OptionalBuild


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

