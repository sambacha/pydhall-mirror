from copy import deepcopy
from hashlib import sha256

import cbor


class Node:
    hash_attrs = []

    def __init__(self, parser=None, offset=None):
        self.offset = offset
        if parser is None:
            self.src = "<string>"
        else:
            self.src = parser.name

    def __hash__(self):
        return hash(
            (self.__class__, self.offset)
            + tuple(self._hash_attr(attr) for attr in self.hash_attrs))

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
                    ) for attr in self.hash_attrs
                ]), offset)

    def __deepcopy__(self, memo):
        return self.__class__(*[deepcopy(getattr(self, a), memo)
                                for a in self.hash_attrs])


class Term(Node):
    _type = None
    _eval = None
    _cbor_idx = None

    def type(self, ctx=None):
        if self._type is None:
            raise NotImplementedError(f"{self.__class__.__name__}.type")
        return self._type

    def eval(self, env=None):
        if self._eval is None:
            raise NotImplementedError(f"{self.__class__.__name__}.eval")
        return self._eval

    def cbor_values(self):
        return [self.eval().as_python()]

    def cbor(self):
        if self._cbor_idx is None:
            raise NotImplementedError(f"{self.__class__.__name__}.cbor")
        return cbor.dumps([self._cbor_idx] + self.cbor_values())

    def sha256(self):
        sha = sha256(self.cbor()).hexdigest()
        return f"sha256:{sha}"

    def subst(self, name: str, replacement: "Term", level: int = 0):
        return self


class Fetchable(Node):
    pass
