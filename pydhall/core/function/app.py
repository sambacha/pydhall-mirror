from ..base import Term, TypeContext, EvalEnv, Value, QuoteContext, Callable
from pydhall.core.type_error import DhallTypeError, TYPE_ERROR_MESSAGE
from .pi import PiValue


class AppValue(Value):
    def __init__(self, fn, arg):
        self.fn = fn
        self.arg = arg

    @classmethod
    def build(cls, *args):
        assert args
        if len(args) == 1:
            return args[0]
        if isinstance(args[0], Callable):
            result = args[0](args[1])
            if result is None:
                result = AppValue(args[0], args[1])
        else:
            result = AppValue(args[0], args[1])

        return AppValue.build(result, *args[2:])

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return App(
            self.fn.quote(ctx, normalize),
            self.arg.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, AppValue):
            return False
        return self.fn.alpha_equivalent(other.fn, level) and self.arg.alpha_equivalent(other.arg, level)

    def copy(self):
        return AppValue(self.fn.copy(), self.arg.copy())


class App(Term):
    # attrs = ['fn', 'arg']
    __slots__ = ['fn', 'arg']
    _cbor_idx = 0
    precedence = 200

    def __init__(self, fn, arg, **kwargs):
        self.fn = fn
        self.arg = arg

    def copy(self, **kwargs):
        new = App(
            self.fn,
            self.arg
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    @classmethod
    def build(cls, *args):
        assert args
        if len(args) == 1:
            return args[0]
        return App.build(App(args[0], args[1]), *args[2:])

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        fn_type = self.fn.type(ctx)
        arg_type = self.arg.type(ctx)
        if not isinstance(fn_type, PiValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.NOT_A_FUNCTION)
        expected_type = fn_type.domain
        if not expected_type @ arg_type:
            # import ipdb; ipdb.set_trace()
            raise DhallTypeError(TYPE_ERROR_MESSAGE.TYPE_MISMATCH % (
                expected_type.quote(), arg_type.quote()))
        return fn_type.codomain(self.arg.eval())

    def subst(self, name: str, replacement: Term, level: int = 0):
        return App(
            self.fn.subst(name, replacement, level),
            self.arg.subst(name, replacement, level))

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return AppValue.build(self.fn.eval(env), self.arg.eval(env))

    def cbor_values(self):
        fn = self.fn
        args = [self.arg.cbor_values()]
        while True:
            if not isinstance(fn, App):
                break
            args = [fn.arg.cbor_values()] + args
            fn = fn.fn
        return [0, fn.cbor_values()] + args

    @classmethod
    def from_cbor(cls, encoded=None, decoded=None):
        assert encoded is None
        assert decoded.pop(0) == cls._cbor_idx
        return App.build(*[Term.from_cbor(decoded=i) for i in decoded])

    def subst(self, name, replacement, level=0):
        return App(
            self.fn.subst(name, replacement, level),
            self.arg.subst(name, replacement, level))

    def rebind(self, local, level=0):
        return App(
            self.fn.rebind(local, level),
            self.arg.rebind(local, level))

    def format_dhall(self):
        return (self.fn.format_dhall(), self.arg.format_dhall())

    def __str__(self):
        return f"{self.fn} {self.arg}"

    def __repr__(self):
        return self.__str__()
