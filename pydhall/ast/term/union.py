from copy import deepcopy

from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from .base import Term, Value, TypeContext, EvalEnv, QuoteContext, Callable
from .universe import TypeValue, UniverseValue, SortValue, KindValue


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

        if len(self) == 0:
            return TypeValue

        first = True
        c = None
        for contructor, typ in self.items():
            if typ is None:
                continue
            k = typ.type(ctx)
            if first:
                if not isinstance(k, UniverseValue):
                    raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_ALTERNATIVE_TYPE)
                c = k
            else:
                if not c @ k:
                    raise DhallTypeError(TYPE_ERROR_MESSAGE.ALTERNATIVE_ANNOTATION_MISMATCH)
            if c == SortValue:
                if typ.eval() != KindValue:
                    raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_ALTERNATIVE_TYPE)
            first = False
        return c


# unionConstructor struct {
#     Type        UnionType
#     Alternative string
# }
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


# unionVal struct {
#     Type        UnionType
#     Alternative string
#     Val         Value // nil for empty alternatives

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
        union_type_val = self.union.type(ctx)

        # handlerType, ok := handlerTypeVal.(RecordType)
        # if !ok {
        #     return nil, mkTypeError(mustMergeARecord)
        # }


        # unionType, ok := unionTypeV.(UnionType)
        # if !ok {
        #     opt, ok := unionTypeV.(OptionalOf)
        #     if !ok {
        #         return nil, mkTypeError(mustMergeUnion)
        #     }
        #     unionType = UnionType{"Some": opt.Type, "None": nil}
        # }
        # if len(handlerType) > len(unionType) {
        #     return nil, mkTypeError(unusedHandler)
        # }

        # if len(handlerType) == 0 {
        #     if t.Annotation == nil {
        #         return nil, mkTypeError(missingMergeType)
        #     }
        #     if _, err := typeWith(ctx, t.Annotation); err != nil {
        #         return nil, err
        #     }
        #     return Eval(t.Annotation), nil
        # }

        # var result Value
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
        # if t.Annotation != nil {
        #     if _, err := typeWith(ctx, t.Annotation); err != nil {
        #         return nil, err
        #     }
        #     if !AlphaEquivalent(result, Eval(t.Annotation)) {
        #         return nil, mkTypeError(annotMismatch(t.Annotation, Quote(result)))
        #     }
        # }
        # return result, nil

