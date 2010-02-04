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


