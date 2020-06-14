from pydhall.ast.base import Term
class DhallCachePoisoned(Exception):
    pass


class ExprCache():
    def __getitem__(self, key):
        if key.hash is not None:
            try:
                expr = self.fetch(key.hash)
            except KeyError:
                pass
            if Term.from_cbor(expr).sha256() != key.hash:
                raise DhallCachePoisoned
        try:
            result = self.fetch(key.cannon, key.import_mode)
            # print("Hit", key)
            return result
        except KeyError:
            # print("Miss", key)
            raise KeyError(key)

    def __setitem__(self, key, value):
        if key.hash is not None:
            self.save(key.hash, value.cbor())
        else:
            self.save(key.cannon, value, key.import_mode)


class InMemoryCache(ExprCache):
    "Cache expression only in memory"
    def __init__(self):
        self._cache = {}

    def fetch(self, key, mode=None):
        return self._cache[(mode, key)]

    def save(self, key, value, mode=None):
        self._cache[(mode, key)] = value


class NullCache(ExprCache):
    "Do not cache"
    def fetch(self, key, mode=None):
        raise KeyError(key)

    def save(self, key, value, mode=None):
        pass

