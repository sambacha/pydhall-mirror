from copy import deepcopy
from hashlib import sha256

import cbor

from .type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class FrozenError(Exception):
    pass


class Node():
    attrs = []

    def __init__(self, *args, parser=None, offset=None, **kwargs):
        i = 0
        for a in self.attrs:
            if a in kwargs:
                val = kwargs.pop(a)
            else:
                val = args[i]
                i += 1
            setattr(self, a, val)
        self.offset = offset
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
        return hash(
            (self.__class__, self.offset)
            + tuple(self._hash_attr(attr) for attr in self.attrs))

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
        for k, v in kwargs:
            object.__setattr__(new, k, v)
        return new


class Term(Node):
    _type = None
    _eval = None
    _cbor_idx = None
    _rebindable = None

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
        return [self._cbor_idx, self.eval().as_python()]

    def cbor(self):
        return cbor.dumps(self.cbor_values())

    def sha256(self):
        sha = sha256(self.cbor()).hexdigest()
        return f"sha256:{sha}"

    def subst(self, name: str, replacement: "Term", level: int = 0):
        return self

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


class Fetchable(Node):
    pass
