from copy import deepcopy
from functools import reduce

import cbor

from .base import Node, Term, _AtomicLit, Builtin, TypeContext, EvalEnv, Op, Var
from .. import value
from ..type_error import DhallTypeError, TYPE_ERROR_MESSAGE
from .double import DoubleLit
from .integer import IntegerLit
from .optional import Some
from .text import Chunk, TextLit, TextTypeValue
from .record.base import RecordLit, RecordType, RecordTypeValue
from .record.ops import CompleteOp, RecordMergeOp
from .natural.base import NaturalLit
from .natural.ops import PlusOp, TimesOp
from .field import Field, Project
from .universe import UniverseValue, TypeValue, KindValue, SortValue
from .union import UnionType, Merge
from .list_.base import List, EmptyList, NonEmptyList, ListOf
from .list_.ops import ListAppendOp


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
        if t.quote().type(ctx) != TypeValue or f.quote().type(ctx) != TypeValue:
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

        # inUniv, err := typeWith(ctx, t.Type)
        # if err != nil {
        #     return nil, err
        # }
        type_type = self.type_.type(ctx)

        # i, ok := inUniv.(Universe)
        # if !ok {
        #     return nil, mkTypeError(invalidInputType)
        # }
        if not isinstance(type_type, UniverseValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_INPUT_TYPE)

        # freshLocal := ctx.freshLocal(t.Label)
        fresh = ctx.freshLocal(self.label)
        outUniv = self.body.subst(self.label, fresh).type(ctx.extend(self.label, self.type_.eval()))
        if not isinstance(outUniv, UniverseValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_OUTPUT_TYPE)
        if outUniv is TypeValue:
            return TypeValue
        if type_type < outUniv:
            return outUniv
        return type_type
        # outUniv, err := typeWith(
        #     ctx.extend(t.Label, Eval(t.Type)),
        #     term.Subst(t.Label, freshLocal, t.Body))
        # if err != nil {
        #     return nil, err
        # }
        # o, ok := outUniv.(Universe)
        # if !ok {
        #     return nil, mkTypeError(invalidOutputType)
        # }
        # return functionCheck(i, o), nil

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


class BoolLit(_AtomicLit):
    _type = value.Bool
    _cbor_idx = -1

    def eval(self, env=None):
        return value.BoolLit(self.value)

    def cbor_values(self):
        return self.value


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


class OrOp(Op):
    precedence = 20
    operators = ("||",)
    _op_idx = 0
    _type = value.Bool

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, value.BoolLit):
            if l:
                return value.True_
            return r
        if isinstance(r, value.BoolLit):
            if r:
                return value.True_
            return l
        if l @ r:
            return l
        return value._OrOp(l, r)


class TextAppendOp(Op):
    precedence = 40
    operators = ("++",)
    _op_idx = 6
    _type = value.Text


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
            return value.True_
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

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        l_type = self.l.type(ctx)
        l_type.quote().assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.INCOMPARABLE_EXPRESSION)
        r_type = self.r.type(ctx)
        r_type.quote().assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.INCOMPARABLE_EXPRESSION)
        if not l_type @ r_type:
            raise DhallTypeError(TYPE_ERROR_MESSAGE, EQUIVALENCE_TYPE_MISMATCH)
        return TypeValue


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
    _eval = SortValue
    _rank = 30

    def type(self):
        raise DhallTypeError(TYPE_ERROR_MESSAGE.UNTYPED)


class Kind(Universe):
    _eval = KindValue
    _type = SortValue
    _rank = 20


class Type(Universe):
    _type = KindValue
    _eval = TypeValue
    _rank = 10


class Text(Builtin):
    _type = TypeValue
    _eval = value.Text


class Bool(Builtin):
    _type = TypeValue
    _eval = value.Bool

    def __init__(self):
        Term.__init__(self)
