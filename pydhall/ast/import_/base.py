import os
from pathlib import Path

from ..base import Term, Node
from ..text.base import PlainTextLit, Text
from ..union import UnionType
from ..function.app import App
from ..field import Field
from .cache import InMemoryCache

CACHE = InMemoryCache()

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

    def __init__(self, hash, import_mode, **kwargs):
        self.hash = hash
        self.import_mode = import_mode

    def copy(self, **kwargs):
        new = Import(
            self.hash,
            self.import_mode
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    class Mode:
        Code = 0
        RawText = 1
        Location = 2

    def resolve(self, *ancestors):
        here = self
        origin = NullOrigin
        if len(ancestors) == 1 and isinstance(ancestors[0], Path):
            ancestors = [LocalFile(ancestors[0])]
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
        if self.import_mode == Import.Mode.Code:
            try:
                return CACHE[here]
            except KeyError:
                pass
        content = here.fetch(origin)
        if self.import_mode == Import.Mode.RawText:
            expr = PlainTextLit(content)
        else:
            from pydhall.parser import parse
            expr = parse(content)
            expr = expr.resolve(*imports)
        _ = expr.type()
        expr = expr.eval().quote()
        # TODO: check hash if provided
        if self.import_mode == Import.Mode.Code:
            CACHE[here] = expr
        return expr


class RemoteFile(Import):
    # attrs = ['url']
    __slots__ = ['url']

    def __init__(self, url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url

    def copy(self, **kwargs):
        new = RemoteFile(
            self.url
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new


    def cbor_values(self):
        scheme = 1 if self.url.scheme == "https" else 0
        result = [
            24,
            self.hash,
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

    def __hash__(self):
        # TODO: canoniacalize the url
        return hash((self.import_mode, self.url))


class EnvVar(Import):
    # attrs = ['name']
    __slots__ = ['name']

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def copy(self, **kwargs):
        new = EnvVar(
            self.name
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new


    def cbor_values(self):
        return [24, self.hash, self.import_mode, 6, self.name]

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

    def __init__(self, path, hash=None, import_mode=0, **kwargs):
        super().__init__(hash, import_mode, **kwargs)
        self.path = path

    def copy(self, **kwargs):
        new = LocalFile(
            self.path
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def origin(self):
        "Origin returns NullOrigin, since EnvVars do not have an origin."
        return NullOrigin

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

    def fetch(self, origin):
        if origin is not NullOrigin:
            raise DhallImportError("Can't get %s from remote import at %s" % (self, origin))
        with open(self.path) as f:
            return f.read()

    def chain_onto(self, base):
        if isinstance(base, LocalFile):
            if self.is_absolute() or self.is_relative_to_home():
                return self
            return LocalFile(get_dir(base.path).joinpath(self.path), None, 0)

        # switch r := base.(type) {
        # case LocalFile:
        #     if l.IsAbs() || l.IsRelativeToHome() {
        #         return l, nil
        #     }
        #     return LocalFile(path.Join(path.Dir(string(r)), string(l))), nil
        # case RemoteFile:
        #     if l.IsAbs() {
        #         return nil, errors.New("Can't get absolute path from remote import")
        #     }
        #     if l.IsRelativeToHome() {
        #         return nil, errors.New("Can't get home-relative path from remote import")
        #     }
        #     newURL := r.url.ResolveReference(l.asRelativeRef())
        #     return RemoteFile{url: newURL}, nil
        # default:
        #     return l, nil
        # }

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
        return [24, self.hash, self.import_mode, path_kind] + parts


class Missing(Import):

    def __init__(self, hash=None, mode=0, **kwargs):
        super().__init__(hash, mode, **kwargs)

    def chain_onto(self, base):
        return Missing()

    def fetch(self, origin):
        raise DhallImportError("Cannot resolve missing import")

    def as_location(self):
        return Field(LOCATION_TYPE, "Missing")

    def cbor_values(self):
        return [24, None, self.import_mode, 7]
