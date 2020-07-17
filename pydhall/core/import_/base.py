import os
from warnings import warn
from pathlib import Path
from urllib.parse import urljoin, quote, urlparse, ParseResult as URL
from urllib import request
from importlib import import_module

from ..base import Term, Node
from ..text.base import PlainTextLit, Text
from ..union import UnionType
from ..function.app import App
from ..field import Field
from .cache import TestFSCache, InMemoryCache, DhallCachePoisoned


CACHE = InMemoryCache()


def set_cache_class(cls):
    global CACHE
    CACHE = cls()


LOCATION_TYPE = UnionType({
    "Local":       Text(),
    "Remote":      Text(),
    "Environment": Text(),
    "Missing":     None,
})

class DhallImportError(Exception):
    pass


NullOrigin = object()


def get_dir(p):
    return Path(os.path.dirname(p))


class Import(Term):
    # attrs = ['hash', 'import_mode']
    __slots__ = ['hash', 'import_mode']
    _cbor_idx = 24

    def __init__(self, hash, import_mode, **kwargs):
        if isinstance(hash, bytearray):
            hash = hash.hex()
        self.hash = hash
        self.import_mode = import_mode

    class Mode:
        Code = 0
        RawText = 1
        Location = 2

    def resolve(self, *ancestors):
        here = self
        origin = NullOrigin
        # allow resolution by Path or url rather than having to create an
        # Import object at call site.
        if len(ancestors) == 1:
            if isinstance(ancestors[0], Path):
                ancestors = [LocalFile(ancestors[0])]
            elif isinstance(ancestors[0], str):
                ancestors = [RemoteFile(urlparse(ancestors[0]))]
        if len(ancestors) >= 1:
            origin = ancestors[-1].origin()
            here = self.chain_onto(ancestors[-1])
        if self.import_mode == Import.Mode.Location:
            return here.as_location()
        for a in ancestors:
            if a == here:
                raise DhallImportError("Detected import cycle in %s" % a)
        imports = list(ancestors)
        imports.append(here)
        try:
            # TODO: check if dhall-golang checks the hash (possible bug in dhall-golang)
            expr = CACHE[here]
            # TODO: hashed import should already be alpha-normalized
            if here.hash and not expr.eval().quote(normalize=True).bin_sha256().hexdigest() == here.hash[4:]:
                raise DhallImportError("Hash mismatch")
            return expr
        except KeyError:
            pass
        except DhallCachePoisoned:
            # TODO: better message
            warn(f"Poisoned cache")
        content = here.fetch(origin)
        if self.import_mode == Import.Mode.RawText:
            expr = PlainTextLit(content)
        elif isinstance(content, Term):
            expr = content
        else:
            from pydhall.parser import parse
            expr = parse(content)
            expr = expr.resolve(*imports)
        # type check the expression
        _ = expr.type()
        # beta-normalize the expression
        # TODO: Should we alpha-normalize here ?
        expr = expr.eval().quote()
        if here.hash and not expr.bin_sha256().hexdigest() == here.hash[4:]:
            raise DhallImportError("Hash mismatch")
        CACHE[here] = expr
        return expr

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded[0] == cls._cbor_idx
        return _CBOR_SCHEMES[decoded[3]].from_cbor(decoded=decoded)


class PydhallSchema(Import):
    __slots__ = ['module', 'cls']
    _cbor_idx = None
    scheme = "pydhall+schema"

    def __init__(self, module, cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = module
        self.cls = cls
        self.cannon = f"{self.scheme}:{self.module}::{self.cls}"

    def copy(self, **kwargs):
        new = PydhallSchema(
            self.module,
            self.cls,
            self.hash,
            self.import_mode,
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def cbor_values(self):
        hash = bytearray.fromhex(self.hash) if self.hash is not None else None
        return [24, hash, self.import_mode, 1001, self.module, self.cls]

    def as_location(self):
        raise DhallImportError(self.scheme + " cannot be imported `as Location`")

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == 24
        return cls(decoded[3], decoded[4], decoded[0], decoded[1])

    def origin(self):
        "Origin returns NullOrigin, since PydhallSchema do not have an origin."
        return NullOrigin

    def __str__(self):
        return f"{self.scheme}:{self.module}::{self.cls}"

    def __hash__(self):
        return hash((self.import_mode, self.module, self.cls))

    def fetch(self, origin):
        """
        Get a record of all the union types and dhall schemas that define the
        target pydhall schema.
        """
        from pydhall.schema import get_library
        from pydhall.core.record.base import RecordLitValue
        mod = import_module(self.module)
        return RecordLitValue(get_library(getattr(mod, self.cls))).quote()

    def chain_onto(self, base):
        return self


class RemoteFile(Import):
    # attrs = ['url']
    __slots__ = ['url']
    _cbor_idx = None

    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parts = Path(url.path.lstrip("/")).parts
        result = []
        # import ipdb; ipdb.set_trace()
        for p in parts:
            if p == ".":
                continue
            elif p == "..":
                if len(result) == 0:
                    result.append(p)
                    continue
                if len(result) == 1 and result[0] == "..":
                    continue
                result.pop()
            else:
                result.append(p)
        path = "/".join(result)
        self.url = URL(url[0], url[1], path, url[3], url[4], url[5])
        self.cannon = self.url.geturl()

    def copy(self, **kwargs):
        new = RemoteFile(
            self.url,
            self.hash,
            self.import_mode,
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def chain_onto(self, base):
        return self

    def fetch(self, origin):
        resp = request.urlopen(self.url.geturl())
        # TODO: implemeent CORS
        return resp.read().decode("utf-8")

    def origin(self):
        return URL(self.url[0], self.url[1], "", "", "", "").geturl()

    def as_location(self):
        return App.build(Field(LOCATION_TYPE, "Remote"), PlainTextLit(self.url.geturl()))

    def cbor_values(self):
        scheme = 1 if self.url.scheme == "https" else 0
        hash = bytearray.fromhex(self.hash) if self.hash is not None else None
        result = [
            24,
            hash,
            self.import_mode,
            scheme,
            None,
            self.url.netloc,
        ]
        parts = self.url.path.strip("/").split("/")
        if len(parts) == 0:
            parts = [""]
        result.extend(parts)
        query = self.url.query if self.url.query else None
        result.append(query)
        return result

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == 24
        hash = decoded.pop(0)
        mode = decoded.pop(0)
        scheme = decoded.pop(0)
        scheme = "http" if scheme == 0 else "https" 
        headers = decoded.pop(0)
        authority = decoded.pop(0)
        parts = decoded[:-1]
        query = decoded[-1]
        query = query if query is not None else ""
        path = "/" + "/".join(parts).strip("/")
        url = URL(scheme, authority, path, "", query, "")
        return cls(url, hash, mode)

    def __hash__(self):
        # TODO: canoniacalize the url
        return hash((self.import_mode, self.url))


class EnvVar(Import):
    # attrs = ['name']
    __slots__ = ['name']
    _cbor_idx = None

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.cannon = "env:" + self.name

    def copy(self, **kwargs):
        new = EnvVar(
            self.name,
            self.hash,
            self.import_mode,
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def cbor_values(self):
        hash = bytearray.fromhex(self.hash) if self.hash is not None else None
        return [24, hash, self.import_mode, 6, self.name]

    def as_location(self):
        return App.build(Field(LOCATION_TYPE, "Environment"), PlainTextLit(self.name))

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == 24
        return cls(decoded[3], decoded[0], decoded[1])

    def origin(self):
        "Origin returns NullOrigin, since EnvVars do not have an origin."
        return NullOrigin

    def __str__(self):
        return f"env:{self.name}"

    def __hash__(self):
        return hash((self.import_mode, self.name))

    def fetch(self, origin):
        """
        Fetch reads the environment variable.  If origin is not NullOrigin,
        an error is returned, to prevent remote imports from importing
        environment variables.
        """
        if origin is not NullOrigin:
            raise DhallImportError("Can't access environment variable from remote import")
        try:
            return os.environ[self.name]
        except KeyError:
            raise DhallImportError("Unset environment variable %s" % self.name)

    def chain_onto(self, base):
        return self


class LocalFile(Import):
    # attrs = ['path']
    __slots__ = ['path']
    _cbor_idx = None

    def __init__(self, path, hash=None, import_mode=0, **kwargs):
        super().__init__(hash, import_mode, **kwargs)
        self.path = path
        self._cannon = None

    @property
    def cannon(self):
        return str(self.path)

    def copy(self, **kwargs):
        new = LocalFile(
            self.path,
            self.hash,
            self.import_mode,
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def origin(self):
        "Origin returns NullOrigin, since EnvVars do not have an origin."
        return NullOrigin

    def as_location(self):
        prefix = "./" if self.is_relative_to_origin() else ("")
        return App.build(
            Field(LOCATION_TYPE, "Local"),
            PlainTextLit(prefix + str(self.path)))

    def __str__(self):
        if self.is_absolute() or self.is_relative_to_home() or self.is_relative_to_parent():
            return str(self.path)
        return f"./{str(self.path)}"

    def __hash__(self):
        return hash((self.import_mode, self.path.resolve()))

    def is_absolute(self):
        return self.path.is_absolute()

    def is_relative_to_home(self):
        return str(self.path).startswith("~")

    def is_relative_to_parent(self):
        return str(self.path).startswith("..")

    def is_relative_to_origin(self):
        return not (
            self.is_absolute()
            or self.is_relative_to_home()
            or self.is_relative_to_parent())

    def as_relative_url(self):
        if self.is_absolute() or self.is_relative_to_home():
            raise ValueError()
        return "/".join([quote(p) for p in self.path.parts])

    def fetch(self, origin):
        if origin is not NullOrigin:
            raise DhallImportError("Can't get %s from remote import at %s" % (self, origin))
        with open(self.path) as f:
            return f.read()

    def chain_onto(self, base):
        if isinstance(base, LocalFile):
            if self.is_absolute() or self.is_relative_to_home():
                return self
            return LocalFile(
                Path(
                    os.path.normpath(
                        get_dir(base.path).joinpath(self.path))),
                    self.hash,
                    self.import_mode)
        if isinstance(base, RemoteFile):
            # TODO: better exception
            if self.is_absolute() or self.is_relative_to_home():
                raise ValueError(self)
            return RemoteFile(urlparse(urljoin(base.url.geturl(), self.as_relative_url())), None, 0)
        return self

    def cbor_values(self):
        parts = list(self.path.parts)
        if self.path.is_absolute():
            path_kind = 2
            parts.pop(0)
        elif parts[0] == "~":
            path_kind = 5
            parts.pop(0)
        elif parts[0] == "..":
            path_kind = 4
            parts.pop(0)
        else:
            path_kind = 3
        hash = bytearray.fromhex(self.hash) if self.hash is not None else None
        return [24, hash, self.import_mode, path_kind] + parts

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == 24
        hash = decoded.pop(0)
        mode = decoded.pop(0)
        kind = decoded.pop(0)
        path = Path(_PATH_KINDS[kind]).joinpath(*decoded)
        return cls(path, hash, mode)


_PATH_KINDS = {2: "/", 3: "", 4: "..", 5: "~"}


class Missing(Import):
    _cbor_idx = None

    def __init__(self, hash=None, mode=0, **kwargs):
        super().__init__(hash, mode, **kwargs)
        self.cannon = None

    def chain_onto(self, base):
        return self

    def fetch(self, origin):
        raise DhallImportError("Cannot resolve missing import")

    def as_location(self):
        return Field(LOCATION_TYPE, "Missing")

    def cbor_values(self):
        return [24, None, self.import_mode, 7]

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == 24
        return cls(mode=decoded[1])


_CBOR_SCHEMES = {
    0: RemoteFile,
    1: RemoteFile,
    2: LocalFile,
    3: LocalFile,
    4: LocalFile,
    5: LocalFile,
    6: EnvVar,
    7: Missing
}
