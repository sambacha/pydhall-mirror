from copy import deepcopy

from pydhall.utils import hash_all
from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from ..base import Term, Value, QuoteContext, EvalEnv, TypeContext, DictTerm
from ..universe import UniverseValue, TypeValue


class RecordLitValue(dict, Value):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return RecordLit({k: v.quote(ctx, normalize) for k, v in self.items()})


class RecordLit(DictTerm):
    def cbor_values(self):
        return [8, {k: self[k].cbor_values() for k in sorted(list(self.keys()))}]

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return RecordLitValue({k: v.eval(env) for k, v in self.items()})

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        rt = RecordTypeValue({k: v.type(ctx) for k, v in self.items()})
        rt.quote().type(ctx)
        return rt

    def __deepcopy__(self, memo):
        return self.__class__(fields={k: deepcopy(v) for k, v in self.items()})

    def subst(self, name: str, replacement: Term, level: int = 0):
        return RecordLit({k: v.subst(name, replacement, level) for k, v in self.items()})

    def rebind(self, local: Term, level: int = 0):
        return RecordLit({k:v.rebind(local, level) for k, v in self.items()})


class RecordTypeValue(dict, Value):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return RecordType({k: v.quote(ctx, normalize) for k, v in self.items()})

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, RecordTypeValue):
            return False
        if len(self) != len(other):
            return False
        for k, v in self.items():
            vo = other.get(k)
            if vo is None or not v.alpha_equivalent(vo, level):
                return False
        return True

    def merge(self, other):
        # var err error
        # result := make(RecordType)
        # for k, v := range l {
        #     result[k] = v
        # }
        result = {k: v for k, v in self.items()}

        # for k, v := range r {
        #     if lField, ok := result[k]; ok {
        #         lSubrecord, Lok := lField.(RecordType)
        #         rSubrecord, Rok := v.(RecordType)
        #         if !(Lok && Rok) {
        #             return nil, errors.New("Record mismatch")
        #         }
        #         result[k], err = mergeRecordTypes(lSubrecord, rSubrecord)
        #         if err != nil {
        #             return nil, err
        #         }
        #     } else {
        #         result[k] = v
        #     }
        # }
        for k, v in other.items():
            try:
                l_field = result[k]
            except KeyError:
                result[k] = v
                continue
            l_is_record_type = isinstance(l_field, RecordTypeValue)
            r_is_record_type = isinstance(v, RecordTypeValue)
            if not (l_is_record_type and r_is_record_type):
                raise DhallTypeError("Record mismatch") # TODO: this is not a type error
            result[k] = l_field.merge(v)

        # return result, nil
        return RecordTypeValue(result)
    # }


class RecordType(DictTerm):
    def cbor_values(self):
        return [7, {k: self[k].cbor_values() for k in sorted(list(self.keys()))}]

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return RecordTypeValue({k: v.eval(env) for k, v in self.items()})

    def __deepcopy__(self, memo):
        return self.__class__(fields={k: deepcopy(v) for k, v in self.items()})

    def subst(self, name: str, replacement: Term, level: int = 0):
        return RecordType({k: v.subst(name, replacement, level) for k, v in self.items()})

    def rebind(self, local: Term, level: int = 0):
        return RecordLit({k:v.rebind(local, level) for k, v in self.items()})

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        universe = TypeValue
        for v in self.values():
            field_universe = v.type(ctx)
            if not isinstance(field_universe, UniverseValue):
                raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_FIELD_TYPE)
            if universe < field_universe:
                universe = field_universe
        return universe


