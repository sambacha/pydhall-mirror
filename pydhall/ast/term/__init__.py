from copy import deepcopy
from functools import reduce


from .base import Node, Term, _AtomicLit, Builtin, TypeContext, EvalEnv, Op, Var
from .. import value
from ..type_error import DhallTypeError, TYPE_ERROR_MESSAGE
from .double.base import DoubleLit
from .integer import IntegerLit
from .optional import Some
from .text.base import Chunk, TextLit, TextTypeValue
from .text.ops import *
from .record.base import RecordLit, RecordType, RecordTypeValue
from .record.ops import CompleteOp, RecordMergeOp
from .natural.base import NaturalLit
from .natural.ops import PlusOp, TimesOp
from .field import Field, Project
from .universe import UniverseValue, TypeValue, KindValue, SortValue, Universe, Sort, Kind, Type
from .union import UnionType, Merge
from .list_.base import List, EmptyList, NonEmptyList, ListOf
from .list_.ops import ListAppendOp
from .boolean.base import Bool, BoolLit, True_, False_, BoolTypeValue
from .boolean.ops import *
from .if_ import If
from .function import Lambda, Pi
from .function.pi import PiValue


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
        if not isinstance(fn_type, PiValue):
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
        # print(repr(self.fn))
        # print(repr(self.arg))
        fn = self.fn
        args = [self.arg.cbor_values()]
        while True:
            if not isinstance(fn, App):
                break
            args = [fn.arg.cbor_values()] + args
            fn = fn.fn
        return [0, fn.cbor_values()] + args

    def subst(self, name, replacement, level=0):
        return App(
            self.fn.subst(name, replacement, level),
            self.arg.subst(name, replacement, level))

    def rebind(self, local, level=0):
        return App(
            self.fn.rebind(local, level),
            self.arg.rebind(local, level))

    def format_dhall(self):
        return (self.fn.format_dhall(), self.arg.format_dhall())


class Annot(Term):
    attrs = ["expr", "annotation"]

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


class Assert(Term):
    attrs = ["annotation"]
    
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


class ToMap(Term):
    attrs = ["record", "type_"]

    def cbor_values(self):
        result = [27, self.record.cbor_values()]
        if self.type_ is not None:
            result += [self.type_.cbor_values()]
        return result

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        # recordTypeVal, err := typeWith(ctx, t.Record)
        # if err != nil {
        #     return nil, err
        # }
        # recordType, ok := recordTypeVal.(RecordType)
        # if !ok {
        #     return nil, mkTypeError(cantAccess)
        # }
        record_type = self.record.type(ctx)
        if not isinstance(record_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_ACCESS)

        # if len(recordType) == 0 {
        #     if t.Type == nil {
        #         return nil, mkTypeError(missingToMapType)
        #     }
        #     err = assertTypeIs(ctx, t.Type, Type, invalidToMapRecordKind)
        #     if err != nil {
        #         return nil, err
        #     }
        #     tVal := Eval(t.Type)
        #     t, ok := listElementType(tVal)
        #     if !ok {
        #         return nil, mkTypeError(invalidToMapType(Quote(tVal)))
        #     }
        #     rt, ok := t.(RecordType)
        #     if !ok || len(rt) != 2 || rt["mapKey"] != Text || rt["mapValue"] == nil {
        #         return nil, mkTypeError(invalidToMapType(Quote(tVal)))
        #     }
        #     return tVal, nil
        # }
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
                    or len(list_type) == 2
                    or list_type.get("mapKey", None) == TextTypeValue
                    or "mapValue" not in list_type):
                # TODO: error message
                raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_TO_MAP_TYPE % type_type.quote())
            return type_type

        # var elemType Value
        elem_type = None
        # for _, v := range recordType {
        #     if elemType == nil {
        #         elemType = v
        #     } else {
        #         if !AlphaEquivalent(elemType, v) {
        #             return nil, mkTypeError(heterogenousRecordToMap)
        #         }
        #     }
        # }
        for v in record_type.values():
            if elem_type is None:
                elem_type = v
            else:
                if not elem_type @ v:
                    raise DhallTypeError(TYPE_ERROR_MESSAGE.HETEROGENOUS_RECORD_TO_MAP)

        # if k, _ := typeWith(ctx, Quote(elemType)); k != Type {
        #     return nil, mkTypeError(invalidToMapRecordKind)
        # }
        if elem_type.quote().type(ctx) != TypeValue:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_TO_MAP_RECORD_KIND)

        # inferred := ListOf{RecordType{"mapKey": Text, "mapValue": elemType}}
        inferred = ListOf(RecordTypeValue({"mapKey": TextTypeValue, "mapValue": elem_type}))

        # if t.Type == nil {
        #     return inferred, nil
        # }
        if self._type is None:
            return inferred

        # if _, err = typeWith(ctx, t.Type); err != nil {
        #     return nil, err
        # }
        _ = self.type_.type(ctx)

        # annot := Eval(t.Type)
        # if !AlphaEquivalent(inferred, annot) {
        #     return nil, mkTypeError(mapTypeMismatch(Quote(inferred), t.Type))
        # }
        if not inferred @ self.type_.eval():
            raise DhallTypeError(TYPE_ERROR_MESSAGE.MAP_TYPE_MISMATCH % ( inferred.quote(), self.type_))

        # return inferred, nil
        return inferred


class ImportAltOp(Op):
    precedence = 10
    operators = ("?",)
    _op_idx = 11


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
            raise DhallTypeError(TYPE_ERROR_MESSAGE, EQUIVALENCE_TYPE_MISMATCH)
        return TypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return EquivOpVal(self.l.eval(env), self.r.eval(env))
