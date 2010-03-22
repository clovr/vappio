from igs.utils.errors import TryError

##
# These are just some simple functions for doing functional style things

def identity(x):
    """A simple identity function"""
    return x

def const(c):
    """Returns a function that takes a parameter and always returns the same value"""
    return lambda _ : c

def applyIfCallable(f, *args, **kwargs):
    """
    Takes a value, and if it is callable applies the arguments to it
    otherwise it simply returns that value
    """

    if callable(f):
        return f(*args, **kwargs)
    else:
        return f


def compose(*funcs):
    """
    Takes a list of functions which takes 1 parameter and composes them.
    compose(f, g)(x) == f(g(x))
    """
    funcs = list(funcs)
    funcs.reverse()
    def _(x):
        v = x
        for f in funcs:
            v = f(v)

        return v

    return _


def tryUntil(count, what, cond):
    """
    Try what until cond returns true or count runs out.
    If count runs it a TryError will be thrown otherwise
    the return value of what is returned
    """
    while count > 0:
        r = what()
        if cond():
            return r

        count -= 1

    raise TryError('Failed', None)

def updateDict(d, nd):
    """
    Adds the key/values in nd to d and returns d
    """
    d.update(nd)
    return d
