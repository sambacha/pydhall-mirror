from copy import deepcopy

import cbor

from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE
from pydhall.utils import dict_to_cbor

from .base import Term, Value, TypeContext, EvalEnv, QuoteContext, Callable
from .universe import TypeValue, UniverseValue, SortValue, KindValue
from .record import RecordTypeValue
from .optional import OptionalOf
from .natural.base import NaturalLitValue
from .function.pi import PiValue


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


class UnionType(dict, Term):

    def __init__(self, alternatives, *args, **kwargs):
        Term.__init__(self, *args, **kwargs)
        dict.__init__(self, alternatives)

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
        return cbor.dumps([11, dict_to_cbor(self)])


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


class Merge(Term):
    attrs = ["handler", "union", "annotation"]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        # handlerTypeVal, err := typeWith(ctx, t.Handler)
        # if err != nil {
        #     return nil, err
        # }
        handler_type = self.handler.type(ctx)

        # unionTypeV, err := typeWith(ctx, t.Union)
        # if err != nil {
        #     return nil, err
        # }
        union_type = self.union.type(ctx)

        # handlerType, ok := handlerTypeVal.(RecordType)
        # if !ok {
        #     return nil, mkTypeError(mustMergeARecord)
        # }
        if not isinstance(handler_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.MUST_MERGE_A_RECORD)

        # unionType, ok := unionTypeV.(UnionType)
        # if !ok {
        #     opt, ok := unionTypeV.(OptionalOf)
        #     if !ok {
        #         return nil, mkTypeError(mustMergeUnion)
        #     }
        #     unionType = UnionType{"Some": opt.Type, "None": nil}
        # }
        if not isinstance(union_type, UnionTypeValue):
            if not isinstance(union_type, OptionalOf):
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MUST_MERGE_UNION)
            union_type = UnionTypeValue({"Some": union_type.type_, "None": None})


        # if len(handlerType) > len(unionType) {
        #     return nil, mkTypeError(unusedHandler)
        # }
        if len(handler_type) > len(union_type):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.UNUSED_HANDLER)

        # if len(handlerType) == 0 {
        #     if t.Annotation == nil {
        #         return nil, mkTypeError(missingMergeType)
        #     }
        #     if _, err := typeWith(ctx, t.Annotation); err != nil {
        #         return nil, err
        #     }
        #     return Eval(t.Annotation), nil
        # }
        if len(handler_type) == 0:
            if self.annotation is None:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISSING_MERGE_TYPE)
            _ = self.annotation.type(ctx)
            return self.annotation.eval()

        # var result Value
        result = None
        # for altName, altType := range unionType {
        #     fieldType, ok := handlerType[altName]
        #     if !ok {
        #         return nil, mkTypeError(missingHandler)
        #     }
        #     if altType == nil {
        #         if result == nil {
        #             result = fieldType
        #         } else {
        #             if !AlphaEquivalent(result, fieldType) {
        #                 return nil, mkTypeError(handlerOutputTypeMismatch(Quote(result), Quote(fieldType)))
        #             }
        #         }
        #     } else {
        #         pi, ok := fieldType.(Pi)
        #         if !ok {
        #             return nil, mkTypeError(handlerNotAFunction)
        #         }
        #         if !AlphaEquivalent(altType, pi.Domain) {
        #             return nil, mkTypeError(handlerInputTypeMismatch(Quote(altType), Quote(pi.Domain)))
        #         }
        #         outputType := pi.Codomain(NaturalLit(1))
        #         outputType2 := pi.Codomain(NaturalLit(2))
        #         if !AlphaEquivalent(outputType, outputType2) {
        #             // hacky way of detecting output type depending on input
        #             return nil, mkTypeError(disallowedHandlerType)
        #         }
        #         if result == nil {
        #             result = outputType
        #         } else {
        #             if !AlphaEquivalent(result, outputType) {
        #                 return nil, mkTypeError(handlerOutputTypeMismatch(Quote(result), Quote(outputType)))
        #             }
        #         }
        #     }
        # }
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
                                outpute_type.quote()))

        # if t.Annotation != nil {
        #     if _, err := typeWith(ctx, t.Annotation); err != nil {
        #         return nil, err
        #     }
        #     if !AlphaEquivalent(result, Eval(t.Annotation)) {
        #         return nil, mkTypeError(annotMismatch(t.Annotation, Quote(result)))
        #     }
        # }
        # return result, nil
        if self.annotation is not None:
            _ = self.annotation.type(ctx)
            if not result @ self.annotation:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.ANNOT_MISMATCH % ( self.annotation, result.quote()))
        return result

