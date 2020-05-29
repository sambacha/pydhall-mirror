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
