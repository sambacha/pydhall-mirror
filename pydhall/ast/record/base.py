from copy import deepcopy

from pydhall.utils import hash_all
from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from ..base import Term, Value, QuoteContext, EvalEnv, TypeContext, DictTerm
from ..universe import UniverseValue, TypeValue


class RecordLitValue(dict, Value):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return RecordLit({k: v.quote(ctx, normalize) for k, v in self.items()})

    def merge(self, other):
        assert isinstance(other, RecordLitValue)
        result = {k: v for k, v in self.items()}
        for k, v in other.items():
            if k in result:
                if isinstance(v, RecordLitValue):
                    result[k] = self[k].merge(v)
            else:
                result[k] = v
        return RecordLitValue(result)

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, RecordLitValue):
            return False
        if len(self) != len(other):
            return False
        for k, v in self.items():
            vo = other.get(k)
            if vo is None or not v.alpha_equivalent(vo, level):
                return False
        return True

    def copy(self):
        return RecordLitValue({k: v.copy() for k, v in self.items()})


class RecordLit(DictTerm):
    _cbor_idx = 8
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

    def copy(self):
        return self.__class__(fields={k: v.copy() for k, v in self.items()})

    def subst(self, name: str, replacement: Term, level: int = 0):
        return RecordLit({k: v.subst(name, replacement, level) for k, v in self.items()})

    def rebind(self, local: Term, level: int = 0):
        return RecordLit({k:v.rebind(local, level) for k, v in self.items()})

    def __str__(self):
        if len(self) == 0:
            return "{=}"
        res = "{ "
        for k, v in self.items():
            res += f"{k} = {v}, "
        return res[:-2] + " }"

    def __repr__(self):
        return self.__str__()


class RecordTypeValue(dict, Value):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return RecordType({k: v.quote(ctx, normalize) for k, v in self.items()})

    def __hash__(self):
        return hash(((k, self[v]) for k in sorted(self.keys())))

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
        result = {k: v for k, v in self.items()}
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

        return RecordTypeValue(result)

    def copy(self):
        return RecordTypeValue({k: v.copy() for k, v in self.items()})


class RecordType(DictTerm):
    _cbor_idx = 7

    def cbor_values(self):
        return [7, {k: self[k].cbor_values() for k in sorted(list(self.keys()))}]

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return RecordTypeValue({k: v.eval(env) for k, v in self.items()})

    # def __deepcopy__(self, memo):
    #     return self.__class__(fields={k: deepcopy(v) for k, v in self.items()})

    def subst(self, name: str, replacement: Term, level: int = 0):
        return RecordType({k: v.subst(name, replacement, level) for k, v in self.items()})

    def rebind(self, local: Term, level: int = 0):
        return RecordType({k:v.rebind(local, level) for k, v in self.items()})

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        universe = TypeValue
        for v in self.values():
            field_universe = v.type(ctx)
            if not isinstance(field_universe, UniverseValue):
                raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_FIELD_TYPE + f": {repr(field_universe)}")
            if universe < field_universe:
                universe = field_universe
        return universe

    def __str__(self):
        if len(self) == 0:
            return "{}"
        res = "{ "
        for k, v in self.items():
            res += f"{k} : {v}, "
        return res[:-2] + " }"

    def __repr__(self):
        return self.__str__()

