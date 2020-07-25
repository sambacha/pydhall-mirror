from copy import deepcopy
from functools import reduce


from .base import Node, Term, _AtomicLit, Builtin, TypeContext, EvalEnv, Op, Var
from .type_error import DhallTypeError, TYPE_ERROR_MESSAGE
from .double.base import DoubleLit
from .integer import IntegerLit
from .optional import Some
from .text.base import Chunk, TextLit, TextTypeValue, PlainTextLitValue
from .text.ops import *
from .record.base import RecordLit, RecordType, RecordTypeValue, RecordLitValue
from .record.ops import CompleteOp, RecordMergeOp, RightBiasedRecordMergeOp
from .natural.base import NaturalLit
from .natural.ops import PlusOp, TimesOp
from .field import Field, Project, ProjectType
from .universe import UniverseValue, TypeValue, KindValue, SortValue, Universe, Sort, Kind, Type
from .union import UnionType, Merge
from .list_.base import List, EmptyList, NonEmptyList, ListOf, EmptyListValue, NonEmptyListValue
from .list_.ops import ListAppendOp
from .boolean.base import Bool, BoolLit, True_, False_, BoolTypeValue, If
from .boolean.ops import *
from .function import Lambda, Pi
from .function.pi import PiValue
from .function.app import App
from .import_.base import Import, EnvVar, LocalFile, RemoteFile, Missing, PydhallSchema
from .import_.ops import ImportAltOp


class Annot(Term):
    # attrs = ['expr', 'annotation']
    __slots__ = ['expr', 'annotation']
    _cbor_idx = 26

    def __init__(self, expr, annotation, **kwargs):
        self.expr = expr
        self.annotation = annotation

    def copy(self, **kwargs):
        new = Annot(
            self.expr,
            self.annotation
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def cbor_values(self):
        return [26, self.expr.cbor_values(), self.annotation.cbor_values()]

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return self.expr.eval(env)

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        if not isinstance(self.annotation, Sort):
            self.annotation.type(ctx)
        actual_type = self.expr.type(ctx)
        if not self.annotation.eval() @ actual_type:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.ANNOT_MISMATCH % (self.annotation, actual_type.quote()))
        return actual_type

    def subst(self, name: str, replacement: Term, level: int =0):
        return self.expr.subst(name, replacement, level)

    def rebind(self, local: Term, level: int =0):
        return self.expr.rebind(local, level)


class AssertValue(Value):
    def __init__(self, annotation):
        self.annotation = annotation

    def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
        ctx = ctx if ctx is not None else QuoteContext()
        return Assert(self.annotation.quote(ctx, normalize))

    def copy(self):
        return AssertValue(self.annotation.copy())


class Assert(Term):
    # attrs = ['annotation']
    __slots__ = ['annotation']
    _cbor_idx = 19
    precedence = 125

    def __init__(self, annotation, **kwargs):
        self.annotation = annotation

    def copy(self, **kwargs):
        new = Assert(
            self.annotation
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def cbor_values(self):
        return [19, self.annotation.cbor_values()]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        self.annotation.assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.NOT_AN_EQUIVALENCE)
        oper = self.annotation.eval()
        if not isinstance(oper, EquivOpVal):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.NOT_AN_EQUIVALENCE)
        if not oper.l @ oper.r:
            raise DhallTypeError(
                TYPE_ERROR_MESSAGE.ASSERTION_FAILED % (
                    oper.l.quote(), oper.r.quote()))
        return oper

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return AssertValue(self.annotation.eval(env))

    def subst(self, name: str, replacement: Term, level: int =0):
        return Assert(self.annotation.subst(name, replacement, level))


class Binding(Node):
    # attrs = ['variable', 'annotation', 'value']
    __slots__ = ['variable', 'annotation', 'value']

    def __init__(self, variable, annotation, value, **kwargs):
        self.variable = variable
        self.annotation = annotation
        self.value = value

    def copy(self, **kwargs):
        new = Binding(
            self.variable,
            self.annotation,
            self.value
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new


class Let(Term):
    # attrs = ['bindings', 'body']
    __slots__ = ['bindings', 'body']
    _cbor_idx = 25

    def __init__(self, bindings, body, **kwargs):
        self.bindings = bindings
        self.body = body

    def copy(self, **kwargs):
        new = Let(
            [b.copy() for b in self.bindings],
            self.body.copy()
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

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
                            binding_type.quote(), binding.annotation))
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
            [
                [
                    b.variable,
                    b.annotation.cbor_values() if b.annotation is not None else None,
                    b.value.cbor_values()
                ]
                for b in self.bindings
            ]
        )
        if isinstance(self.body, Let):
            return [25] + bindings + self.body.cbor_values()[1:]
        else:
            return [25] + bindings + [self.body.cbor_values()]

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == cls._cbor_idx
        bindings = []
        while len(decoded) > 3:
            var = decoded.pop(0)
            annot = Term.from_cbor(decoded=decoded.pop(0))
            val = Term.from_cbor(decoded=decoded.pop(0))
            bindings.append(Binding(var, annot, val))
        assert len(decoded) == 1
        return Let(bindings, Term.from_cbor(decoded=decoded[0]))

    # def resolve(self, *ancestors):
    #     bindings = []
    #     for b in self.bindings:
    #         variable = b.variable
    #         if b.annotation is not None:
    #             annotation = b.annotation.resolve(*ancestors)
    #         else:
    #             annotation = None
    #         value = b.value.resolve(*ancestors)
    #         bindings.append(Binding(variable, annotation, value))
    #     return Let(bindings, self.body.resolve(*ancestors))


class ToMapValue(Value):
    def __init__(self, record, type_=None):
        self.record = record
        self.type_ = type_

    def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
        ctx = ctx if ctx is not None else QuoteContext()
        if self.type_ is not None:
            type_ = self.type_.quote(ctx, normalize)
        else:
            type_ = None
        return ToMap(self.record.quote(ctx, normalize), type_)

    def copy(self):
        if self.type_ is not None:
            type = self.type_.copy()
        else:
            type = None
        return ToMapValue(self.record.copy(), type)
    

class ToMap(Term):
    # attrs = ['record', 'type_']
    __slots__ = ['record', 'type_']
    _cbor_idx = 27

    def __init__(self, record, type_, **kwargs):
        self.record = record
        self.type_ = type_

    def copy(self, **kwargs):
        new = ToMap(
            self.record,
            self.type_
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def cbor_values(self):
        result = [27, self.record.cbor_values()]
        if self.type_ is not None:
            result += [self.type_.cbor_values()]
        return result

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == cls._cbor_idx
        decoded = [Term.from_cbor(decoded=i) for i in decoded]
        if len(decoded) == 1:
            decoded.append(None)
        return ToMap(*decoded)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()

        record = self.record.eval(env)

        if isinstance(record, RecordLitValue):
            if len(record) == 0:
                return EmptyListValue(self.type_.eval(env))
            field_names = list(sorted(record.keys()))
            result = [
                RecordLitValue({
                    "mapKey": PlainTextLitValue(name),
                    "mapValue": record[name]})
                for name in field_names]
            return NonEmptyListValue(result)

        if self.type_ is not None:
            type = self.type_.eval(env)
        else:
            type = None
        return ToMapValue(record, type)

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        record_type = self.record.type(ctx)
        if not isinstance(record_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_ACCESS + f": `{repr(self.record)}")

        if len(record_type) == 0:
            if self.type_ is None:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_TO_MAP_TYPE)
            self.type_.assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.INVALID_TO_MAP_RECORD_KIND)
            type_type = self.type_.eval()
            if not isinstance(type_type, ListOf):
                # TODO: error message
                raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_TO_MAP_TYPE % type_type.quote())
            list_type = type_type.type_
            if not (isinstance(list_type, RecordTypeValue)
                    and len(list_type) == 2
                    and list_type.get("mapKey", None) == TextTypeValue
                    and "mapValue" in list_type):
                # TODO: error message
                raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_TO_MAP_TYPE % type_type.quote())
            return type_type

        elem_type = None
        for v in record_type.values():
            if elem_type is None:
                elem_type = v
            else:
                if not elem_type @ v:
                    raise DhallTypeError(TYPE_ERROR_MESSAGE.HETEROGENOUS_RECORD_TO_MAP)

        if elem_type.quote().type(ctx) != TypeValue:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_TO_MAP_RECORD_KIND)

        inferred = ListOf(RecordTypeValue({"mapKey": TextTypeValue, "mapValue": elem_type}))

        if self.type_ is None:
            return inferred

        _ = self.type_.type(ctx)

        if not inferred @ self.type_.eval():
            raise DhallTypeError(TYPE_ERROR_MESSAGE.MAP_TYPE_MISMATCH % ( inferred.quote(), self.type_))

        return inferred

    def subst(self, name: str, replacement: Term, level: int =0):
        if self.type_ is not None:
            type = self.type_.subst(name, replacement, level)
        else:
            type = None
        return ToMap(self.record.subst(name, replacement, level), type)

    def rebind(self, local: Term, level: int =0):
        if self.type_ is not None:
            type = self.type_.rebind(local, level)
        else:
            type = None
        return ToMap(self.record.rebind(local, level), type)


class EquivOpVal(OpValue):
    def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
        ctx = ctx if ctx is not None else QuoteContext()
        return EquivOp(
            self.l.quote(ctx, normalize),
            self.r.quote(ctx, normalize))


class EquivOp(Op):
    precedence = 130
    operators = ("≡", "===")
    _op_idx = 12

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        l_type = self.l.type(ctx)
        l_type.quote().assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.INCOMPARABLE_EXPRESSION)
        r_type = self.r.type(ctx)
        r_type.quote().assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.INCOMPARABLE_EXPRESSION)
        if not l_type @ r_type:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.EQUIVALENCE_TYPE_MISMATCH)
        return TypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return EquivOpVal(self.l.eval(env), self.r.eval(env))
