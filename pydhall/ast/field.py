from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from .base import Term, Value, TypeContext, EvalEnv, QuoteContext

from .record.base import RecordTypeValue, RecordLitValue
from .record.ops import RecordMergeOpValue, RightBiasedRecordMergeOpValue
from .union import UnionTypeValue, UnionType, UnionConstructor, UnionVal
from .function.pi import PiValue


class ProjectType(Term):
    # attrs = ['record', 'selector']
    __slots__ = ['record', 'selector']

    def __init__(self, record, selector, **kwargs):
        self.record = record
        self.selector = selector

    def copy(self, **kwargs):
        new = ProjectType(
            self.record,
            self.selector
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        record_type = self.record.type(ctx)
        if not isinstance(record_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_PROJECT)

        _ = self.selector.type(ctx)
        selector = self.selector.eval()
        if not isinstance(selector, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_PROJECT_BY_EXPRESSION)

        result = {}
        for name, typ in selector.items():
            try:
                field_type = record_type[name]
            except KeyError:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_FIELD + f" `{name}`")
            if not field_type @ typ:
                raise DhallTypeError(
                    TYPE_ERROR_MESSAGE.PROJECTION_TYPE_MISMATCH % (
                        typ.quote(), field_type.quote()))
            result[name] = typ
        return RecordTypeValue(result)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()

        s = self.selector.eval(env)
        field_names = list(s.keys())
        return Project(self.record, field_names).eval(env)

    def cbor_values(self):
        return [10, self.record.cbor_values(), [self.selector.cbor_values()]]

    def subst(self, name: str, replacement: Term, level: int = 0):
        return ProjectType(
            self.record.subst(name, replacement, level),
            self.selector.subst(name, replacement, level)
        )

    def rebind(self, local, level=0):
        return ProjectType(
            self.record.rebind(local, level),
            self.selector.rebind(local, level)
        )


class ProjectValue(Value):
    def __init__(self, record, field_names):
        self.record = record
        self.field_names = field_names

    def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
        ctx = ctx if ctx is not None else QuoteContext()
        return Project(self.record.quote(ctx, normalize), self.field_names)

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, ProjectValue):
            return False
        if len(self.field_names) != len(other.field_names):
            return False
        for i, name in enumerate(self.field_names):
            if name != other.field_names[i]:
                return False
        return self.record.alpha_equivalent(other.record, level)

    def copy(self):
        return ProjectValue(self.record.copy(), self.field_names)


class Project(Term):
    # attrs = ['record', 'field_names']
    __slots__ = ['record', 'field_names']
    _cbor_idx = 10

    def __init__(self, record, field_names, **kwargs):
        self.record = record
        self.field_names = field_names

    def copy(self, **kwargs):
        new = Project(
            self.record,
            self.field_names
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        record_type = self.record.type(ctx)
        if not isinstance(record_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_PROJECT)
        fields = {}
        for name in self.field_names:
            if name in fields:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.DUPLICATE_PROJECT_FIELD % name)
            try:
                fields[name] = record_type[name]
            except KeyError:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_FIELD + f" `{name}`")
        return RecordTypeValue(fields)

    def cbor_values(self):
        return [10, self.record.cbor_values()] + self.field_names

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == cls._cbor_idx
        record = Term.from_cbor(decoded=decoded.pop(0))
        proj = decoded[0]
        if isinstance(proj[0], list):
            return ProjectType(record, Term.from_cbor(decoded=proj[0]))
        return cls(record, decoded)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()

        record = self.record.eval(env)
        self.field_names.sort()

        # Simplifications
        while True:
            if isinstance(record, ProjectValue):
                record = record.record
                continue
            if isinstance(record, RightBiasedRecordMergeOpValue):
                if isinstance(record.r, RecordLitValue):
                    not_overriden = []
                    overrides = {}
                    for name in self.field_names:
                        if name in record.r:
                            overrides[name] = record.r[name]
                        else:
                            not_overriden.append(name)
                    if not not_overriden:
                        return RecordLitValue(overrides)
                    return RightBiasedRecordMergeOpValue(
                        ProjectValue(record.l, not_overriden),
                        RecordLitValue(overrides))
            break

        # empty projections result in empty records
        if not self.field_names:
            return RecordLitValue({})

        # apply the projection
        if isinstance(record, RecordLitValue):
            return RecordLitValue({k: record[k] for k in self.field_names})

        # Not a record. Can't fully evaluate yet.
        return ProjectValue(record, self.field_names)

    def subst(self, name: str, replacement: Term, level: int = 0):
        return Project(self.record.subst(name, replacement, level), self.field_names)

    def rebind(self, local, level: int = 0):
        return Project(
            self.record.rebind(local, level), self.field_names)


class FieldValue(Value):
    def __init__(self, record, field_name):
        self.record = record
        self.field_name = field_name

    def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
        ctx = ctx if ctx is not None else QuoteContext()
        return Field(self.record.quote(ctx, normalize), self.field_name)

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        if self.field_name != other.field_name:
            return False
        return self.record.alpha_equivalent(other.record, level)

    def copy(self):
        return FieldValue(self.record.copy(), self.field_name)


class Field(Term):
    # attrs = ['record', 'field_name']
    __slots__ = ['record', 'field_name']
    _cbor_idx = 9

    def __init__(self, record, field_name, **kwargs):
        self.record = record
        self.field_name = field_name

    def copy(self, **kwargs):
        new = Field(
            self.record,
            self.field_name
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new


    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        record_type = self.record.type(ctx)
        if isinstance(record_type, RecordTypeValue):
            if self.field_name not in record_type:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_FIELD + f" `{self.field_name}`")
            return record_type[self.field_name]
        union_type = self.record.eval()
        if not isinstance(union_type, UnionTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_ACCESS + f": `{repr(self.record)}.{self.field_name}")
        try:
            alternative_type = union_type[self.field_name]
        except KeyError:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_CONSTRUCTOR)
        if alternative_type is None:
            return union_type
        return PiValue(
            self.field_name,
            alternative_type,
            lambda _: union_type)

    def cbor_values(self):
        return [9, self.record.cbor_values(), self.field_name]

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == cls._cbor_idx
        return cls(Term.from_cbor(decoded=decoded[0]), decoded[1])

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        record = self.record.eval(env)

        # simplifications
        while True:
            if isinstance(record, ProjectValue):
                record = record.record
                continue
            if isinstance(record, RecordMergeOpValue):
                if isinstance(record.l, RecordLitValue):
                    if self.field_name in record.l:
                        return FieldValue(
                            RecordMergeOpValue(
                                RecordLitValue({self.field_name: record.l[self.field_name]}),
                                record.r),
                            self.field_name)
                    record = record.r
                    continue
                if isinstance(record.r, RecordLitValue):
                    if self.field_name in record.r:
                        return FieldValue(
                            RecordMergeOpValue(
                                record.l,
                                RecordLitValue({self.field_name: record.r[self.field_name]})),
                            self.field_name)
                    record = record.l
                    continue
            elif isinstance(record, RightBiasedRecordMergeOpValue):
                if isinstance(record.l, RecordLitValue):
                    if self.field_name in record.l:
                        return FieldValue(
                            RightBiasedRecordMergeOpValue(
                                RecordLitValue({self.field_name: record.l[self.field_name]}),
                                record.r),
                            self.field_name)
                    record = record.r
                    continue
                if isinstance(record.r, RecordLitValue):
                    if self.field_name in record.r:
                        return record.r[self.field_name]
                    record = record.l
                    continue
            break

        if isinstance(record, RecordLitValue):
            return record[self.field_name]

        if isinstance(record, UnionTypeValue):
            if record[self.field_name] is None:
                return UnionVal(record, self.field_name)
            return UnionConstructor(record, self.field_name)

        return FieldValue(record, self.field_name)

    def subst(self, name: str, replacement: Term, level: int = 0):
        return Field(self.record.subst(name, replacement, level), self.field_name)

    def rebind(self, local, level: int = 0):
        return Field(self.record.rebind(local, level), self.field_name)

