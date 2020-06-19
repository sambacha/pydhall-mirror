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

    def __hash__(self):
        return hash((k, v) for k, v in self.items())


class EvalEnv(dict):
    def copy(self):
        result = {}
        for k, v in self.items():
            result[k] = [i.copy() for i in v]
        return EvalEnv(result)

    def insert(self, name, value):
        self.setdefault(name, []).insert(0, value)


class Value:
    _quote = None
    attrs = None

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

    def copy(self):
        assert False, f"{self.__class__}"


class Callable(Value):
    def __call__(self, arg):
        raise NotImplementedError(f"{self.__class__.__name__}.__call__")


class DependentValue(Value):
    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.type_)})"


class FrozenError(Exception):
    pass


class BuiltinValue(Value):
    __slots__ = ["name"]

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

    def copy(self):
        return self


class Node():
    attrs = []

    def __hash__(self):
        return hash_all([getattr(self, attr) for attr in self.__slots__])

    def _hash_attr(self, name):
        attr = getattr(self, name)
        if isinstance(attr, list):
            return hash(tuple(item for item in attr))
        return hash(attr)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return self.__class__.__name__ + "(%s)" % (
            ", ".join(["%s=%s" % (
                    attr, repr(getattr(self, attr))
                    ) for attr in self.__slots__
                ]))

    # TODO: clean this ugly mess
    def resolve(self, *ancestors):
        try:
            if not self.__slots__:
                return self
        except AttributeError:
            return self
        attrs = {}
        for name in self.__slots__:
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

        def _decode_from_class(_cls, data):
            if _cls.from_cbor.__func__ is Term.from_cbor.__func__:
                # the class doesn't implement it's own from_cbor, we
                # call the constructor.
                return _cls(*[Term.from_cbor(decoded=i) for i in data[1:]])
            else:
                # we let the class dealing with the data
                return _cls.from_cbor(decoded=data)

        if decoded is None:
            if encoded is None:
                return None
            decoded = cbor.loads(encoded)
            if isinstance(decoded, cbor.Tag):
                decoded = decoded.value
        if isinstance(decoded, bool):
            return Term._cbor_indexes[-1](decoded)  # BoolLit
        elif isinstance(decoded, int):
            return Term._cbor_indexes[-4]("_", decoded) # Var
        elif isinstance(decoded, list):
            # TODO: these Tag unwrapings are made solely to
            # make the tests pass. Check the standard way
            # to deal with those once all is migrated to cbor2
            if isinstance(decoded[0], cbor.Tag):
                decoded[0] = decoded[0].value
            try:
                term_cls = cls._cbor_indexes[decoded[0]]
            except KeyError:
                assert isinstance(decoded[0], str)
                if isinstance(decoded[1], cbor.Tag):
                    decoded[1] = decoded[1].value
                return cls._cbor_indexes[-4](*decoded) # Var
            return _decode_from_class(term_cls, decoded)
        elif isinstance(decoded, str):
            term_cls = Term._cbor_indexes[decoded]
            return _decode_from_class(term_cls, [])
        elif isinstance(decoded, float):
            return Term._cbor_indexes[-3](decoded)  # DoubleLit
        assert False

    def bin_sha256(self):
        return sha256(self.cbor())

    def sha256(self):
        sha = self.bin_sha256().hexdigest()
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

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._cbor_idx is not None:
            Term._cbor_indexes[cls._cbor_idx] = cls

    def __hash__(self):
        return hash_all(self)

    def resolve(self, *ancestors):
        return self.__class__({k: v.resolve(*ancestors) for k,v in self.items()})

    def copy(self):
        return self.__class__(fields={k: v.copy() for k, v in self.items()})

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == cls._cbor_idx
        return cls({k: Term.from_cbor(decoded=v) for k, v in decoded[0].items()})


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
            # __slots__ = ["arrity", "_call", "fn_class", "args"]
            def __init__(self, arrity, call, fn_class, args=None):
                self.arrity = arrity
                self._call = call
                self.fn_class = fn_class
                self.args = args if args is not None else []

            def copy(self):
                if self.args is None:
                    args = None
                else:
                    args = [i.copy() for i in self.args]
                return self.__class__(self.arrity, self._call, self.fn_class, args)

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
    _cbor_idx = None
    _by_name = {}
    _literal_name = None

    def __init_subclass__(cls, /, **kwargs):
        if cls._literal_name is not None:
            key = cls._literal_name
        else:
            key = cls.__name__.strip("_")
        cls._cbor_idx = key
        # if key == "Natural":
        #     import ipdb; ipdb.set_trace()
        Builtin._by_name[key] = cls
        super().__init_subclass__(**kwargs)

    def __hash__(self):
        return hash(self.__class__)

    def __init__(self, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if name is not None:
            self.__class__ = Builtin._by_name[name]

    def __str__(self):
        if self._literal_name is not None:
            return self._literal_name
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    def copy(self):
        return self

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
    # attrs = ['value']
    __slots__ = ['value']

    def __init__(self, value, **kwargs):
        self.value = value

    def copy(self, **kwargs):
        new = self.__class__(
            self.value
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        if decoded is None:
            1/0
            decoded = cbor.loads(encoded)
        return cls(decoded[1])

    def format_dhall(self):
        return (str(self.value),)

    def subst(self, name: str, replacement: Term, level: int = 0):
        return self

    def rebind(self, *args, **kwargs):
        return self


class OpValue(Value):
    __slots__ = ["l", "r"]

    def __init__(self, l, r):
        self.l = l
        self.r = r

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.l.alpha_equivalent(other.l, level)
            and self.r.alpha_equivalent(other.r, level))

    def copy(self):
        return self.__class__(self.l.copy(), self.r.copy())


class Op(Term):
    # attrs = ['l', 'r']
    __slots__ = ['l', 'r']
    _rebindable = ["l", "r"]
    _cbor_idx = 3

    _cbor_op_indexes = {}


    def __init__(self, l, r, **kwargs):
        self.l = l
        self.r = r

    def copy(self, **kwargs):
        new = self.__class__(
            self.l,
            self.r
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        Op._cbor_op_indexes[cls._op_idx] = cls

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        if decoded is None:
            1/0
            decoded = cbor.loads(encoded)
        return cls._cbor_op_indexes[decoded[1]](
            *[Term.from_cbor(decoded=i) for i in decoded[2:]])

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

    def __str__(self):
        return f"{self.l} {self.operators[0]} {self.r}"


class _FreeVar(Value):
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        return Var(self.name, self.index)

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        return other.__class__ is _FreeVar and self.index == other.index and self.name == other.name

    def copy(self):
        return _FreeVar(self.name, self.index)


class Var(Term):
    # attrs = ['name', 'index']
    __slots__ = ['name', 'index']
    _cbor_idx = -4

    def __init__(self, name, index, **kwargs):
        self.name = name
        self.index = index

    def copy(self, **kwargs):
        new = Var(
            self.name,
            self.index
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def __hash__(self):
        return hash((self.name, self.index))

    def rebind(self, *args, **kwargs):
        return self

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
    # attrs = ['name', 'index']
    __slots__ = ['name', 'index']

    def __init__(self, name, index, **kwargs):
        self.name = name
        self.index = index

    def copy(self, **kwargs):
        new = LocalVar(
            self.name,
            self.index
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new


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
    __slots__ = ["name", "index"]

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        return LocalVar(self.name, self.index)

    def alpha_equivalent(self, other: "Value", level: int = 0) -> bool:
        return other.__class__ is LocalVarValue and self.index == other.index and self.name == other.name

    def copy(self):
        return LocalVarValue(self.name, self.index)

    def __repr__(self):
        return f"LocalVarValue({self.name}, {self.index})"
