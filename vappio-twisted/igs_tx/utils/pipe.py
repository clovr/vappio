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

def runPipeCurry(m):
    return lambda initialValue : runPipe(m, initialValue)
    
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

def emit(v):
    raise ReturnValue(v)

def ret(v):
    return v

def const(c):
    """
    Shorthand for lambda c : lambda _ : ret(c)
    """
    return lambda _ : ret(c)

def hookError(f, onError):
    """
    Returns a function that will call f, and if f throws an exception calls onError and reraises the exception.
    Example:
    
    f = lambda s : s + ' world'
    onError = lambda e : sys.stdout.write(str(e) + '\n')
    print hookError(f, onError)('hello')

    This will print 'hello world'.  If we change f to:

    f = lambda _ : raise Exception()

    hookError will raise an exception after printing the string represenation of the
    exception to stdout.

    If an error happens in onError, that is what will be raised
    """
    def _(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ReturnValue:
            # Don't hook the error in this case
            raise
        except Exception, err:
            onError(err, *args, **kwargs)
            raise

    return _
