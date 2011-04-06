#
# This implements the ability to compose and pipe functions so that they can
# short circuit the pipe/composition with a value to return

class ReturnValue(Exception):
    """
    This is used to short circuit the valuation
    and return ret
    """
    def __init__(self, ret):
        self.ret = ret

def runPipe(m, initialValue):
    try:
        return m(initialValue)
    except ReturnValue, retv:
        return retv.ret

def pipe(fs):
    """
    Functional piping:
    pipe([f, g])(x) == g(f(x))
    """
    def _(v):
        t = v
        for f in fs:
            t = f(t)

        return t

    return _

def compose(fs):
    """
    Functional composition:
    compose([f, g])(x) = f(g(x))
    """
    fs = list(fs)
    fs.reverse()
    return pipe(fs)

def returnValue(v):
    raise ReturnValue(v)
