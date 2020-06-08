from io import BytesIO
import struct

import cbor


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
