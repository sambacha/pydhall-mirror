from .term.base import Value, BuiltinValue, QuoteContext, Callable, OpValue


class _App(Value):
    def __init__(self, fn, arg):
        self.fn = fn
        self.arg = arg

    @classmethod
    def build(cls, *args):
        assert args
        # print("***********")
        # print(args)
        if len(args) == 1:
            return args[0]
        # if args[1] == 13.37:
        #     import ipdb; ipdb.set_trace()
        if isinstance(args[0], Callable):
            # try to apply the function
            result = args[0](args[1])
            if result is None:
                # print("None")
                result = _App(args[0], args[1])
        else:
            result = _App(args[0], args[1])

        return _App.build(result, *args[2:])

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .term import App
        # print("-------------")
        # print(repr(self.fn))
        # print(repr(self.arg))
        return App(
            self.fn.quote(ctx, normalize),
            self.arg.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, _App):
            return False
        return self.fn.alpha_equivalent(other.fn, level) and self.arg.alpha_equivalent(other.arg, level)

