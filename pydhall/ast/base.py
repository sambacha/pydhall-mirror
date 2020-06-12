from copy import deepcopy
from hashlib import sha256
from functools import reduce

import cbor
import cbor2

from pydhall.utils import hash_all, cbor_dumps
from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class QuoteContext(dict):
    def extend(self, name):
        new = QuoteContext(self)
        new[name] = self.get(name, 0) + 1
        return new


class TypeContext(dict):
    def extend(self, name, value):
        ctx = self.__class__()
        for k, v in self.items():
            ctx[k] = list(v)
        ctx.setdefault(name, []).append(value)
        return ctx

    def freshLocal(self, name):
        return LocalVar(name=name, index=len(self.get(name, tuple())))


class EvalEnv(dict):
    def copy(self):
        return deepcopy(self)

    def insert(self, name, value):
        self.setdefault(name, []).insert(0, value)


class Value:
    _quote = None

    def __str__(self):
        return str(self.as_python())

    @classmethod
    def from_python(cls, value):
        cls(value)

    def alpha_equivalent(self, other: "Value", level: int = 0) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__}.alpha_equivalent")

    def __matmul__(self, other):
        return self.alpha_equivalent(other)

    def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> "Term":
        if self._quote is None:
            raise NotImplementedError(f"{self.__class__.__name__}.quote")
        return self._quote


class Callable(Value):
    def __call__(self, arg):
        raise NotImplementedError(f"{self.__class__.__name__}.__call__")


class DependentValue(Value):
    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.type_)})"


class FrozenError(Exception):
    pass


class BuiltinValue(Value):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"BuiltinValue({self.name})"

    def __str__(self):
        self.name

    def quote(self, ctx=None, normalize=False):
        return Builtin(self.name)

    def alpha_equivalent(self, other, level=0):
        return other.name is self.name


class Node():
    attrs = []

    def __init__(self, *args, parser=None, offset=None, **kwargs):
        self.offset = offset
        i = 0
        for a in self.attrs:
            if a in kwargs:
                val = kwargs.pop(a)
            else:
                val = args[i]
                i += 1
            setattr(self, a, val)
        if parser is None:
            self.src = "<string>"
        else:
            self.src = parser.name

    def __setattr__(self, name, value):
        if not hasattr(self, name) or name in ["__class__", "parser", "offset"]:
            super().__setattr__(name, value)
        else:
            raise FrozenError(name)

    def __hash__(self):
        return hash_all([getattr(self, attr) for attr in self.attrs])
        # return hash(
        #     (self.__class__, self.offset)
        #     + tuple(self._hash_attr(attr) for attr in self.attrs))

    def _hash_attr(self, name):
        attr = getattr(self, name)
        if isinstance(attr, list):
            return hash(tuple(item for item in attr))
        return hash(attr)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        offset = ", offset=%s" % self.offset if self.offset is not None else ""
        return self.__class__.__name__ + "(%s%s)" % (
            ", ".join(["%s=%s" % (
                    attr, repr(getattr(self, attr))
                    ) for attr in self.attrs
                ]), offset)

    def __deepcopy__(self, memo):
        return self.__class__(*[deepcopy(getattr(self, a), memo)
                                for a in self.attrs])

    def copy(self, **kwargs):
        new = deepcopy(self)
        for k, v in kwargs.items():
            object.__setattr__(new, k, v)
        return new

    def resolve(self, *ancestors):
        if not self.attrs:
            return self
        attrs = {}
        for name in self.attrs:
            val = getattr(self, name)
            if isinstance(val, Node):
                attrs[name] = val.resolve(*ancestors)
            elif isinstance(val, (int, float, str)) or val is None:
                attrs[name] = val
            elif isinstance(val, list):
                res = []
                for i in val:
                    if isinstance(i, Node):
                        res.append(i.resolve(*ancestors))
                    elif isinstance(i, (int, float, str)) or val is None:
                        res.append(i)
                    else:
                        assert False
                attrs[name] = res
            else:
                assert False, f"resolve() should be implemented for {self.__class__} - {name} - {val.__class__}"

        return self.copy(**attrs)


class Term(Node):
    _type = None
    _eval = None
    _cbor_idx = None
    _rebindable = None

    _cbor_indexes = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._cbor_idx is not None:
            Term._cbor_indexes[cls._cbor_idx] = cls

    def type(self, ctx=None):
        if self._type is None:
            raise NotImplementedError(f"{self.__class__.__name__}.type")
        return self._type

    def eval(self, env=None):
        if self._eval is None:
            raise NotImplementedError(f"{self.__class__.__name__}.eval")
        return self._eval

    def cbor_values(self):
        if self._cbor_idx is None:
            raise NotImplementedError(f"{self.__class__.__name__}.cbor_values")
        if self._cbor_idx < 0:
            return self.eval().as_python()
        return [self._cbor_idx, self.eval().as_python()]

    def cbor(self):
        return cbor_dumps(self.cbor_values())
        # return cbor2.dumps(self.cbor_values(), canonical=True)

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        if decoded is None:
            decoded = cbor.loads(encoded)
        if isinstance(decoded, list):
            term_cls = cls._cbor_indexes[decoded[0]]
            if term_cls.from_cbor.__func__ is Term.from_cbor.__func__:
                return term_cls(
                    *[Term.from_cbor(i) for i in decoded[1:]])
            else:
                return term_cls.from_cbor(decoded=decoded)
        elif isinstance(decoded, bool):
            return Term._cbor_indexes[-1](decoded)  # BoolLit
        elif isinstance(decoded, str):
            try:
                return Term._cbor_indexes[-2](decoded)  # Builtin
            except KeyError:
                return Term._cbor_indexes[-4](*decoded)
        elif isinstance(decoded, float):
            return Term._cbor_indexes[-3](decoded)  # DoubleLit
        assert False


    def sha256(self):
        sha = sha256(self.cbor()).hexdigest()
        return f"sha256:{sha}"

    def subst(self, name: str, replacement: "Term", level: int = 0):
        raise NotImplementedError(f"{self.__class__.__name__}.subst")
        # return self

    def rebind(self, local, level=0):
        """
        Find all instances of `local` and replaces them with the equivalent
        Var. Returns self if nothing is changed, otherwise return a copy of
        the original term
        """
        if self._rebindable is None:
            raise NotImplementedError(f"{self.__class__.__name__}.rebind")
        if len(self._rebindable) == 0:
            return self
        args = {}
        for attr_name in self._rebindable:
            attr = getattr(self, attr_name)
            if attr is not None:
                args[attr_name] = attr.rebind(local, level)
        return self.copy(**args)

    def assertType(self, expected, ctx, msg):
        tp = self.type(ctx)
        if not tp @ expected:
            raise DhallTypeError(msg)
        return tp

    def format_dhall(self):
        raise NotImplementedError(f"{self.__class__.__name__}.format_dhall")

    def dhall(self):
        format = self.format_dhall()
        # print(format)
        def reduce_format(agg, elem=None):
            if isinstance(agg, tuple):
                agg = reduce(reduce_format, agg)
            if elem is None:
                return agg
            if isinstance(elem, tuple):
                return f"{agg} {reduce(reduce_format, elem)}"
            else:
                return f"{agg} {elem}"
        return reduce(reduce_format, format)


class DictTerm(dict, Term):
    def __init__(self, fields, *args, **kwargs):
        Term.__init__(self, *args, **kwargs)
        dict.__init__(self, fields)

    def __hash__(self):
        return hash_all(self)

    def resolve(self, *ancestors):
        return self.__class__({k: v.resolve(*ancestors) for k,v in self.items()})


class BuiltinMeta(type):
    @classmethod
    def _get_arrity(cls, tp):
        from . import Pi, App
        if isinstance(tp, Pi):
            return 1 + cls._get_arrity(tp.body)
        return 0
        
    def __new__(cls, name, bases, attrs):
        if name == "Builtin":
            return type.__new__(cls, name, bases, attrs)

        if not isinstance(attrs.get("_type"), str):
            return type.__new__(cls, name, bases, attrs)

        from pydhall.parser.base import Dhall
        _type_ast = Dhall.p_parse(attrs.pop("_type"))
        _type = _type_ast.eval()

        def _new_type_fn(self, ctx=None):
            return _type

        # TODO: Make this a metaclass rather than passing the state
        # arround
        class val(Callable):
            def __init__(self, arrity, call, fn_class, args=None):
                self.arrity = arrity
                self._call = call
                self.fn_class = fn_class
                self.args = args if args is not None else []

            def __call__(self, x: Value) -> Value:
                args = list(self.args)
                args.append(x)
                if len(args) < self.arrity:
                    return self.__class__(self.arrity, self._call, self.fn_class, args)
                return self._call(self, *args)

            def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
                ctx = ctx if ctx is not None else QuoteContext()
                from . import App
                return App.build(self.fn_class(), *[a.quote(ctx, normalize) for a in self.args])

            def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
                if self._call != other._call:
                    return False
                if self.fn_class != other.fn_class:
                    return False
                if len(self.args) != len(other.args):
                    return False
                for i, a in enumerate(self.args):
                    if not a.alpha_equivalent(other.args[i], level):
                        return False
                return True

        call = attrs.pop("__call__")

        new_cls = type.__new__(cls, name, bases, attrs)

        new_cls.type = _new_type_fn
        new_cls._eval = val(cls._get_arrity(_type_ast), call, new_cls)

        return new_cls


class Builtin(Term, metaclass=BuiltinMeta):
    _cbor_idx = -2
    _by_name = {}
    _literal_name = None

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._literal_name is not None:
            key = cls._literal_name
        else:
            key = cls.__name__.strip("_")
        Builtin._by_name[key] = cls

    def __init__(self, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if name is not None:
            self.__class__ = Builtin._by_name[name]

    def __str__(self):
        return self.__class__.__name__

    def rebind(self, local, level=0):
        return self

    def cbor_values(self):
        if self._literal_name is not None:
            return self._literal_name
        else:
            return self.__class__.__name__.strip("_")

    def format_dhall(self):
        name = self._literal_name if self._literal_name is not None else self.__class__.__name__.strip("_")
        return (name,)

    def subst(self, name: str, replacement: Term, level: int = 0):
        return self


class _AtomicLit(Term):
    attrs = ["value"]

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        if decoded is None:
            decoded = cbor.loads(encoded)
        return cls(decoded[1])

    def format_dhall(self):
        return (str(self.value),)

    def subst(self, name: str, replacement: Term, level: int = 0):
        return self

    def rebind(self, *args, **kwargs):
        return self


class OpValue(Value):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.l.alpha_equivalent(other.l, level)
            and self.r.alpha_equivalent(other.r, level))


class Op(Term):
    attrs = ["l", "r"]
    _rebindable = ["l", "r"]
    _cbor_idx = 3

    _cbor_op_indexes = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        Op._cbor_indexes[cls._op_idx] = cls

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        if decoded is None:
            decoded = cbor.loads(encoded)
        return cls._cbor_op_indexes[decoded[1]](
            *[Term.from_cbor(i) for i in decoded[2:]])

    def type(self, ctx=None):
        if self._type is not None:
            ctx = ctx if ctx is not None else TypeContext()
            self.r.assertType(self._type, ctx, TYPE_ERROR_MESSAGE.CANT_OP % (self.operators[0], self._type.__class__.__name__))
            self.l.assertType(self._type, ctx, TYPE_ERROR_MESSAGE.CANT_OP % (self.operators[0], self._type.__class__.__name__))
            return self._type
        raise NotImplementedError(f"{self.__class__.__name__}.type")

    def cbor_values(self):
        return [3, self._op_idx, self.l.cbor_values(), self.r.cbor_values()]

    def subst(self, name: str, replacement: "Term", level: int = 0):
        return self.__class__(
            self.l.subst(name, replacement, level),
            self.r.subst(name, replacement, level),
        )

    def rebind(self, local, level=0):
        return self.__class__(
            self.l.rebind(local, level),
            self.r.rebind(local, level),
        )


class _FreeVar(Value):
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        return Var(self.name, self.index)

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        return other.__class__ is _FreeVar and self.index == other.index and self.name == other.name


class Var(Term):
    attrs = ["name", "index"]
    _rebindable = []
    _cbor_idx = -4

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        max_idx = len(env.get(self.name, tuple()))
        if self.index >= max_idx:
            return _FreeVar(self.name, self.index - max_idx)
        return env[self.name][self.index]

    def subst(self, name: str, replacement: "Term", level: int = 0):
        if self.name == name and self.index == level:
            return replacement
        return self

    def cbor_values(self):
        if self.name == "_":
            return self.index
        return [self.name, self.index]

    def type(self, ctx=None):
        raise DhallTypeError(
            TYPE_ERROR_MESSAGE.UNBOUND_VARIABLE % self.name)

    def __str__(self):
        index = "" if not self.index else f"@{self.index}"
        return f"{self.name}{index}"

    def format_dhall(self):
        return (self.__str__(),)


class LocalVar(Term):
    attrs = ["name", "index"]

    def type(self, ctx=None):
        assert ctx is not None
        vals = ctx.get(self.name)
        assert vals is not None
        try:
            return vals[self.index]
        except IndexError:
            raise DhallTypeError(
                TYPE_ERROR_MESSAGE.UNBOUND_VARIABLE % self.name)

    def eval(self, env=None):
        return LocalVarValue(self.name, self.index)

    def rebind(self, local, level=0):
        if local.name == self.name and local.index == self.index:
            return Var(self.name, level)
        return self

    def subst(self, name: str, replacement: "Term", level: int = 0):
        return self


class LocalVarValue(Value):
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        return LocalVar(self.name, self.index)

    def alpha_equivalent(self, other: "Value", level: int = 0) -> bool:
        return other.__class__ is LocalVarValue and self.index == other.index and self.name == other.name
