##
# These are just some simple functions for doing functional style things

def id(x):
    """A simple identity function"""
    return x

def const(c):
    """Returns a function that takes a parameter and always returns the same value"""
    return lambda _ : c
