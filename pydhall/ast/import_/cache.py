import os
from pathlib import Path

from pydhall.ast.base import Term


class DhallCachePoisoned(Exception):
    pass


class ExprCache():
    def __getitem__(self, key):
        if key.hash is not None:
            try:
                expr = self.fetch_hash(key.hash)
            except KeyError:
                pass
            else:
                if expr.bin_sha256().hexdigest() != key.hash[4:]:
                    raise DhallCachePoisoned
                return expr
        if key.cannon is not None:  # Only for Missing
            try:
                result = self.fetch_name(key.cannon, key.import_mode)
                # print("Hit", key.import_mode)
                return result
            except KeyError:
                # print("Miss", key.import_mode)
                raise KeyError(key)
        raise KeyError(key)

    def __setitem__(self, key, value):
        if key.hash is not None:
            self.save_hash(key.hash, value.cbor())
        if key.cannon is None:  # Missing
            return
        else:
            self.save_name(key.cannon, value, key.import_mode)


class InMemoryCache(ExprCache):
    "Cache expressions only in memory, Only for testing purpose."
    def __init__(self):
        self._cache = {}

    def fetch_hash(self, key):
        return self._fetch(key, None)

    def fetch_name(self, key, mode=None):
        return self._fetch(key, mode)

    def save_hash(self, key, value):
        return self._save(key, value, 0)

    def save_name(self, key, value, mode=None):
        return self._save(key, value, mode)

    def _fetch(self, key, mode):
        return self._cache[(mode, key)]

    def _save(self, key, value, mode):
        self._cache[(mode, key)] = value


class FSCache(ExprCache):
    def __init__(self):
        self.root = self.get_cache_root()
        self.name_cache = {}

    def get_cache_root(self):
        path = os.environ.get("XDG_CACHE_HOME", None)
        if path is None:
            root = Path.home().joinpath(".cache/dhall")
        else:
            root = Path(path).joinpath("dhall")
        if not os.path.exists(root):
            os.makedirs(root)
        return root

    def fetch_hash(self, key, mode=None):
        path = self.root.joinpath(key)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return Term.from_cbor(f.read())
        raise KeyError(key)

    def fetch_name(self, key, mode=None):
        return self.name_cache[(mode, key)]

    def save_hash(self, key, value, mode=None):
        path = self.root.joinpath(key)
        if os.path.exists(self.root.joinpath()):
            return False
        with open(path, "wb") as f:
            f.write(value.cbor())
        return True

    def save_name(self, key, value, mode=None):
        self.name_cache[(mode, key)] = value
        return True


class TestFSCache(FSCache):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created = []

    def save_hash(self, key, value, mode=None):
        if super().save_hash(key, value, mode):
            self.created.append[key]

    def reset(self):
        for k in self.created:
            os.unlink(self.root.joinpath(k))
        self.created = []


class NullCache(ExprCache):
    "Do not cache"
    def fetch(self, key, mode=None):
        raise KeyError(key)

    def save(self, key, value, mode=None):
        pass

