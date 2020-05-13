from .base import Node, Term


class If(Term):
    hash_attrs = ["cond", "true", "false"]

    def __init__(self, cond, true, false, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cond = cond
        self.true = true
        self.false = false


class Annot(Term):
    hash_attrs = ["expr", "annotation"]

    def __init__(self, expr, annotation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expr = expr
        self.annotation = annotation


class Var(Term):
    hash_attrs = ["name", "index"]

    def __init__(self, name, index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.index = index


class NumberLit(Term):
    hash_attrs = ["value"]

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value


class NaturalLit(NumberLit):
    pass


class DoubleLit(NumberLit):
    pass


class IntegerLit(NumberLit):
    pass


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


class EmptyList(Term):
    hash_attrs = ["type"]

    def __init__(self, type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = type


class Some(Term):
    hash_attrs = ["val"]

    def __init__(self, val, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val = val


class ToMap(Term):
    hash_attrs = ["record", "type"]

    def __init__(self, record, type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self.type = type


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


class Builtin(Term):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__ = _builtin_cls[name]


class Double(Builtin):
    pass


class Text(Builtin):
    pass


class Bool(Builtin):
    pass


class Natural(Builtin):
    pass


class Integer(Builtin):
    pass


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

