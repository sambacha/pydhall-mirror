from io import BytesIO
import struct

import cbor
import cbor2


def hash_dict(d):
    return hash(tuple((k, hash_all(v)) for k, v in sorted(d.items())))

def hash_list(l):
    return hash(tuple(hash_all(i) for i in l))

def hash_all(o):
    if isinstance(o, dict):
        return hash_dict(o)
    if isinstance(o, list):
        return hash_list(o)
    return hash(o)

def dict_to_cbor(d):
    out = BytesIO()

    length = list(cbor.dumps(len(d)))
    length[0] = length[0] ^ b'\xa0'[0]
    out.write(bytearray(length))
    for k in sorted(d):
        out.write(cbor.dumps(k))
        try:
            out.write(cbor.dumps(d[k].cbor()))
        except AttributeError:
            out.write(cbor.dumps(d[k]))
    return out.getvalue()

def cbor_dict(d):
    result = {}
    for k in sorted(d):
        try:
            val = d[k].cbor_values()
        except AttributeError:
            val = d[k]
        result[k] = val
    return result

from cbor2 import encoder

def _encode_canonical_map(self, value):
    "Reorder keys according to Canonical CBOR specification"
    self.encode_length(5, len(value))
    for k in sorted(value.keys()):
        self.encode(k)
        val = value[k]
        try:
            val = val.cbor_values()
        except AttributeError:
            pass
        self.encode(val)


encoder.canonical_encoders[dict] = _encode_canonical_map


def cbor_dump(obj, f):
    encoder.CBOREncoder(f, canonical=True).encode(obj)

from io import BytesIO
def cbor_dumps(obj):
    with BytesIO() as f:
        cbor_dump(obj, f)
        return f.getvalue()


class visitor:
    def __init__(self, *cls):
        self.cls = cls

    def __call__(self, fn):
        fn._visitor_class = self.cls
        return fn


class Visitor:
    _visitor = None

    def __init_subclass__(cls,**kwargs):
        super().__init_subclass__(**kwargs)
        cls._visitor = {}
        for name in dir(cls):
            attr = getattr(cls, name)
            if hasattr(attr, "_visitor_class"):
                for target in attr._visitor_class:
                    cls._visitor[target] = attr

    def visit(self, sh):
        key = None
        try:
            if sh in self._visitor:
                key = sh
        except TypeError:  # probably a dict or a list
            pass
        if key is None:
            if isinstance(sh, type):
                tp = sh
            else:
                tp = sh.__class__
            for cls in tp.__mro__[:-1]:
                if cls in self._visitor:
                    key = cls
                    break
        method = self._visitor.get(key, self.__class__.visit_generic)
        return method(self, sh)
