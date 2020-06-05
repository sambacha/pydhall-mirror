from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from .base import Term, Value, TypeContext, EvalEnv

from .record.base import RecordTypeValue, RecordLitValue
from .record.ops import RecordMergeOpValue, RightBiasedRecordMergeOpValue
from .union import UnionTypeValue, UnionType, UnionConstructor

class ProjectValue(Value):
    pass


class Project(Term):
    attrs = ["record", "field_names"]

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
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_FIELD)
        return RecordTypeValue(fields)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()

        # record := evalWith(t.Record, e)
        record = self.record.eval(env)

        # fieldNames := t.FieldNames
        # sort.Strings(fieldNames)
        self.field_names.sort()

        # // simplifications
        # for {
        #     if proj, ok := record.(project); ok {
        #         record = proj.Record
        #         continue
        #     }
        #     op, ok := record.(oper)
        #     if ok && op.OpCode == term.RightBiasedRecordMergeOp {
        #         if r, ok := op.R.(RecordLit); ok {
        #             notOverridden := []string{}
        #             overrides := RecordLit{}
        #             for _, fieldName := range fieldNames {
        #                 if override, ok := r[fieldName]; ok {
        #                     overrides[fieldName] = override
        #                 } else {
        #                     notOverridden = append(notOverridden, fieldName)
        #                 }
        #             }
        #             if len(notOverridden) == 0 {
        #                 return overrides
        #             }
        #             return oper{
        #                 OpCode: term.RightBiasedRecordMergeOp,
        #                 L: project{
        #                     Record:     op.L,
        #                     FieldNames: notOverridden,
        #                 },
        #                 R: overrides,
        #             }
        #         }
        #     }

        #     break
        # }
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

        # if lit, ok := record.(RecordLit); ok {
        #     result := make(RecordLit)
        #     for _, k := range fieldNames {
        #         result[k] = lit[k]
        #     }
        #     return result
        # }
        if isinstance(record, RecordLitValue):
            return RecordLitValue({k: record[k] for k in self.field_names})

        # if len(fieldNames) == 0 {
        #     return RecordLit{}
        # }
        if not self.field_names:
            return RecordLitValue({})

        # return project{
        #     Record:     record,
        #     FieldNames: fieldNames,
        # }
        return ProjectValue(record, self.fieldNames)

    def subst(self, name: str, replacement: Term, level: int = 0):
        return Project(self.record.subst(name, replacement, level), self.field_names)


class FieldValue(Value):
    def __init__(self, record, label):
        self.record = record
        self.label = label


class Field(Term):
    attrs = ["record", "field_name"]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        record_type = self.record.type(ctx)
        if isinstance(record_type, RecordTypeValue):
            if self.field_name not in record_type:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_FIELD)
            return record_type[self.field_name]
        union_type = self.record.eval()
        if not isinstance(union_type, UnionTypeValue):
            raise DhallTypeError(CANT_ACCESS)
        try:
            alternative_type = union_type[self.field_name]
        except KeyError:
            raise DhallTypeError(MISSING_CONSTRUCTOR)
        if alternative_type is None:
            return union_type
        from ..value import Pi
        return Pi(
            self.field_name,
            alternative_type,
            lambda _: union_type)

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
        return Project(self.record.subst(name, replacement, level), self.field_name)

