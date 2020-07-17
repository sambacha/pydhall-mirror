from copy import deepcopy

import cbor

from pydhall.core.type_error import DhallTypeError, TYPE_ERROR_MESSAGE
from pydhall.utils import cbor_dict

from .base import Term, Value, TypeContext, EvalEnv, QuoteContext, Callable, DictTerm
from .universe import TypeValue, UniverseValue, SortValue, KindValue
from .record.base import RecordTypeValue, RecordLitValue
from .optional import OptionalOf, SomeValue, NoneOf
from .natural.base import NaturalLitValue
from .function.pi import PiValue
from .function.app import App, AppValue


class UnionTypeValue(dict, Value):

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        result = {}
        for k, v in self.items():
            if v is None:
                result[k] = None
            else:
                result[k] = v.quote(ctx, normalize)
        return UnionType(result)

    def __hash__(self):
        return hash(((k, self[v]) for k in sorted(self.keys())))

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, UnionTypeValue):
            return False
        if len(self) != len(other):
            return False
        for k, v in self.items():
            if v is None:
                if other[k] is not None:
                    return False
                continue
            if not v.alpha_equivalent(other[k], level):
                return False
        return True

    def copy(self):
        result = {}
        for k, v in self.items():
            if v is None:
                result[k] = None
            else:
                result[k] = v.copy()
        return UnionTypeValue(result)


class UnionType(DictTerm):
    _cbor_idx = 11

    def __deepcopy__(self, memo):
        return self.__class__(alternatives={k: deepcopy(v) for k, v in self.items()})

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        result = UnionTypeValue()
        for k, v in self.items():
            if v is None:
                result[k] = None
            else:
                result[k] = v.eval(env)
        return result

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        universe = TypeValue
        for contructor, typ in self.items():
            if typ is None:
                continue
            k = typ.type(ctx)
            if not isinstance(k, UniverseValue):
                raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_ALTERNATIVE_TYPE)
            if k > universe:
                universe = k
        return universe

    def cbor_values(self):
        return [11, cbor_dict(self)]

    def subst(self, name: str, replacement: Term, level: int = 0):
        result = {}
        for k, v in self.items():
            if v is not None:
                v = v.subst(name, replacement, level)
            result[k] = v
        return UnionType(result)

    def rebind(self, local, level=0):
        result = {}
        for k, v in self.items():
            if v is not None:
                v = v.rebind(local, level)
            result[k] = v
        return UnionType(result)

    def resolve(self, *ancestors):
        result = {}
        for k, v in self.items():
            if v is None:
                result[k] = v
            else:
                result[k] = v.resolve(*ancestors)
        return UnionType(result)

    def copy(self, **kwargs):
        result = {}
        for k, v in self.items():
            if v is None:
                result[k] = v
            else:
                result[k] = v.copy()
        return UnionType(result)


class UnionConstructor(Callable):
    def __init__(self, type_, alternative):
        self.type_ = type_
        self.alternative = alternative

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .field import Field
        return Field(
            self.type_.quote(ctx, normalize),
            self.alternative)

    def __call__(self, v: Value):
        return UnionVal(self.type_, self.alternative, v)


class UnionVal(Value):
    def __init__(self, type_, alternative, val=None):
        self.type_ = type_
        self.alternative = alternative
        self.val = val

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, UnionVal):
            return False
        if self.alternative != other.alternative:
            return False
        if self.val is not None:
            if other.val is None:
                return False
            if not self.val.alpha_equivalent(other.val, level):
                return False
        return self.type_.alpha_equivalent(other.type_, level)

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .field import Field
        result = Field(self.type_.quote(ctx, normalize), self.alternative)
        if self.val is not None:
            return App(result, self.val.quote(ctx, normalize))
        return result

    def copy(self):
        val = self.val.copy() if self.val is not None else None
        return UnionVal(self.type_.copy(), self.alternative, val)


class MergeValue(Value):
    def __init__(self, handler, union, annotation=None):
        self.handler = handler
        self.union = union
        self.annotation = annotation

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        h = self.handler.quote(ctx, normalize)
        u = self.union.quote(ctx, normalize)
        if self.annotation:
            a = self.annotation.quote(ctx, normalize)
        else:
            a = None
        return Merge(h, u, a)

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, UnionVal):
            return False
        if self.annotation:
            if not other.annotation:
                return False
            if not self.annotation.alpha_equivalent(other.annotation, level):
                return False
        if not self.union.alpha_equivalent(other.union, level):
            return False
        if not self.handler.alpha_equivalent(other.handler, level):
            return False
        return True

    def copy(self):
        if self.annotation is not None:
            annot = self.annotation.copy()
        else:
            annot = None
        return MergeValue(self.handler.copy(), self.union.copy(), annot)


class Merge(Term):
    # attrs = ['handler', 'union', 'annotation']
    __slots__ = ['handler', 'union', 'annotation']
    _cbor_idx = 6

    def __init__(self, handler, union, annotation, **kwargs):
        self.handler = handler
        self.union = union
        self.annotation = annotation

    def copy(self, **kwargs):
        new = Merge(
            self.handler,
            self.union,
            self.annotation
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def cbor_values(self):
        if self.annotation is not None:
            return [6, self.handler.cbor_values(),
                    self.union.cbor_values(), self.annotation.cbor_values()]
        return [6, self.handler.cbor_values(), self.union.cbor_values()]

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == cls._cbor_idx
        if len(decoded) == 2:
            decoded.append(None)
        return Merge(*[Term.from_cbor(decoded=i) for i in decoded])

    def subst(self, name: str, replacement: Term, level: int = 0):
        h = self.handler.subst(name, replacement, level)
        u = self.union.subst(name, replacement, level)
        if self.annotation:
            a = self.annotation.subst(name, replacement, level)
        else:
            a = None
        return Merge(h, u, a)

    def rebind(self, local, level=0):
        h = self.handler.rebind(local, level)
        u = self.union.rebind(local, level)
        if self.annotation:
            a = self.annotation.rebind(local, level)
        else:
            a = None
        return Merge(h, u, a)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        handlers = self.handler.eval(env)
        union = self.union.eval(env)
        if isinstance(handlers, RecordLitValue):
            if isinstance(union, UnionVal):
                if union.val is None:
                    return handlers[union.alternative]
                return AppValue.build(handlers[union.alternative], union.val)
            if isinstance(union, SomeValue):
                return AppValue.build(handlers["Some"], union.value)
            if isinstance(union, NoneOf):
                return handlers["None"]
        if self.annotation is not None:
            annot = self.annotation.eval(env)
        else:
            annot = None
        return MergeValue(handlers, union, annot)

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        handler_type = self.handler.type(ctx)

        union_type = self.union.type(ctx)

        if not isinstance(handler_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.MUST_MERGE_A_RECORD)

        if not isinstance(union_type, UnionTypeValue):
            if not isinstance(union_type, OptionalOf):
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MUST_MERGE_UNION)
            union_type = UnionTypeValue({"Some": union_type.type_, "None": None})


        if len(handler_type) > len(union_type):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.UNUSED_HANDLER)

        if len(handler_type) == 0:
            if self.annotation is None:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_MERGE_TYPE)
            _ = self.annotation.type(ctx)
            return self.annotation.eval()

        result = None

        for alt_name, alt_type in union_type.items():
            try:
                field_type = handler_type[alt_name]
            except KeyError:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_HANDLER)
            if alt_type is None:
                if result is None:
                    result = field_type
                else:
                    if not result @ field_type:
                        raise DhallTypeError(
                            TYPE_ERROR_MESSAGE.HANDLER_OUTPUT_TYPE_MISMATCH % (
                                result.quote(),
                                field_type.quote()))
            else:
                if not isinstance(field_type, PiValue):
                    raise DhallTypeError(TYPE_ERROR_MESSAGE.HANDLER_NOT_A_FUNCTION)
                if not alt_type @ field_type.domain:
                    raise DhallTypeError(
                        TYPE_ERROR_MESSAGE.HANDLER_INPUT_TYPE_MISMATCH % (
                            alt_type.quote(),
                            field_type.quote()))
                output_type = field_type.codomain(NaturalLitValue(1))
                output_type2 = field_type.codomain(NaturalLitValue(2))
                if not output_type @ output_type2:
                    raise DhallTypeError(TYPE_ERROR_MESSAGE.DISALLOWED_HANDLER_TYPE)
                if result is None:
                    result = output_type
                else:
                    if not result @ output_type:
                        raise DhallTypeError(
                            TYPE_ERROR_MESSAGE.HANDLER_OUTPUT_TYPE_MISMATCH % (
                                result.quote(),
                                output_type.quote()))

        if self.annotation is not None:
            _ = self.annotation.type(ctx)
            if not result @ self.annotation.eval():
                raise DhallTypeError(TYPE_ERROR_MESSAGE.ANNOT_MISMATCH % ( self.annotation, result.quote()))
        return result

