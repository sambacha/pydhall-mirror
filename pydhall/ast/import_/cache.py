class DhallCachePoisoned(Exception):
    pass


class ExprCache():
    def __getitem__(self, key):
        if key.hash is not None:
            try:
                expr = self.fetch(key.hash)
            except KeyError:
                pass
            if expr.sha256() != key.hash:
                raise DhallCachePoisoned
        try:
            return self._cache[key.cannon]
        except KeyError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        if key.hash is not None:
            self.save(key.hash, value)
        else:
            self.save(key.cannon, value)


class InMemoryCache(ExprCache):
    "Cache expression only in memory"
    def __init__(self):
        self._cache = {}

    def fetch(self, key):
        return self._cache[key]

    def save(self, key, value):
        self._cache[key] = value


class NullCache(ExprCache):
    "Do not cache"
    def fetch(self, key):
        raise KeyError(key)

    def save(self, key, value):
        pass

