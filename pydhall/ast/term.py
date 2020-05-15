from .base import Node, Term
import cbor
from . import value
from .type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class If(Term):
    hash_attrs = ["cond", "true", "false"]

    def __init__(self, cond, true, false, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cond = cond
        self.true = true
        self.false = false

    def eval(self, env=None):
        env = env if env is not None else {}
        cond = self.cond.eval(env)
        if cond is value.True_:
            return self.true.eval()
        if cond is value.False_:
            return self.false.eval()

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
    hash_attrs = ["expr", "annotation"]

    def __init__(self, expr, annotation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expr = expr
        self.annotation = annotation


class Var(Term):
    hash_attrs = ["name", "index"]

    def __init__(self, name, index=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.index = index

    def eval(self, env=None):
        env = env if env is not None else {}
        max_idx = len(env.get(self.name, tuple()))
        if self.index >= max_idx:
            return value._FreeVar(self.name, self.index - max_idx)
        return env[self.name][self.index]


class _AtomicLit(Term):
    hash_attrs = ["value"]

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value


class NaturalLit(_AtomicLit):
    _type = value.Natural

    def eval(self, env=None):
        env = env if env is not None else {}
        return value.NaturalLit(self.value)


class DoubleLit(_AtomicLit):
    _type = value.Double

    def eval(self, env=None):
        env = env if env is not None else {}
        return value.DoubleLit(self.value)


class IntegerLit(_AtomicLit):
    _type = value.Integer

    def eval(self, env=None):
        env = env if env is not None else {}
        return value.IntegerLit(self.value)


class BoolLit(_AtomicLit):
    _type = value.Bool

    def eval(self, env=None):
        env = env if env is not None else {}
        return value.BoolLit(self.value)


class Chunk(Node):
    hash_attrs = ["prefix", "expr"]

    def __init__(self, prefix, expr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = prefix
        self.expr = expr


class TextLit(Term):
    hash_attrs = ["chunks", "suffix"]

    def __init__(self, chunks, suffix, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chunks = chunks
        self.suffix = suffix


class Import(Term):
    hash_attrs = ["import_hashed", "import_mode"]

    class Mode:
        Code = 0
        RawText = 1
        Location = 2

    def __init__(self, import_hashed, import_mode=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.import_hashed = import_hashed
        self.import_mode = import_mode


class Binding(Node):
    hash_attrs = ["variable", "annotation", "value"]

    def __init__(self, variable, annotation, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.variable = variable
        self.annotation = annotation
        self.value = value


class Let(Term):
    hash_attrs = ["bindings", "body"]

    def __init__(self, bindings, body, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bindings = bindings
        self.body = body

    def eval(self, env=None):
        env = {} if env is None else dict(env)
        for b in self.bindings:
            env[b.variable] = [b.value.eval(env)] + list(env.get(b.variable, []))
        return self.body.eval(env)


class EmptyList(Term):
    hash_attrs = ["type_"]

    def __init__(self, type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type__ = type


class Some(Term):
    hash_attrs = ["val"]

    def __init__(self, val, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val = val


class ToMap(Term):
    hash_attrs = ["record", "type_"]

    def __init__(self, record, type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self.type_ = type


class Merge(Term):
    hash_attrs = ["handler", "union", "annotation"]

    def __init__(self, handler, union, annotation=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handler = handler
        self.union = union
        self.annotation = annotation


class Op(Term):
    hash_attrs = ["l", "r"]

    def __init__(self, l, r, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.l = l
        self.r = r


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


class Double(Builtin):
    _type = value.Type


class Text(Builtin):
    _type = value.Type


class Bool(Builtin):
    _type = value.Type


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

