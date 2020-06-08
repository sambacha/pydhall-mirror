from .term.base import Fetchable


class EnvVar(Fetchable):
    attrs = ["name"]


class LocalFile(Fetchable):
    attrs = ["path"]


class ImportHashed(Fetchable):
    attrs = ["fetchable", "hash"]
