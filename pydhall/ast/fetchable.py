from .term.base import Fetchable


class EnvVar(Fetchable):
    hash_attrs = ["name"]

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name


class LocalFile(Fetchable):
    hash_attrs = ["path"]

    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path


class ImportHashed(Fetchable):
    hash_attrs = ["fetchable", "hash"]

    def __init__(self, fetchable, hash, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetchable = fetchable
        self.hash = hash
