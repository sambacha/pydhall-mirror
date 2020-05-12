class Node:
    hash_attrs = []

    def __init__(self, parser=None, offset=None):
        self.offset = offset
        if parser is None:
            self.src = "<string>"
        else:
            self.src = parser.name

    def __hash__(self):
        return hash(
            (self.__class__, self.offset)
            + tuple(self._hash_attr(attr) for attr in self.hash_attrs))

    def _hash_attr(self, name):
        attr = getattr(self, name)
        if isinstance(attr, list):
            return hash(tuple(item for item in attr))
        return hash(attr)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        offset = ", offset=%s" % self.offset if self.offset is not None else ""
        return self.__class__.__name__ + "(%s%s)" % (
            ", ".join(["%s=%s" % (
                    attr, repr(getattr(self, attr))
                    ) for attr in self.hash_attrs
                ]), offset)


class Comment(Node):
    hash_attrs = ["content"]

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content


class LineComment(Comment):
    pass


class BlockComment(Comment):
    pass


class Term(Node):
    pass


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


class Op(Term):
    def __init__(self, op, first, rest, *args, **kwargs):
        super().__init__(*args, **kwargs)


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

