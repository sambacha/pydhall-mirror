class InMemoryCache:
    def __init__(self):
        self._cache = {}

    def __getitem__(self, key):
        if key.hash is not None:
            try:
                return self._cache[key.hash]
            except KeyError:
                pass
        return self._cache[key]

    def __setitem__(self, key, value):
        if key.hash is not None:
            self._cache.hash = value
        self._cache[key] = value

