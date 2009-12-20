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

