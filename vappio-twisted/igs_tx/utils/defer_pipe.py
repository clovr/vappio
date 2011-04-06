#
# This is the same as pipe, except each functions must be a deferred

from igs_tx.utils import pipe

def runPipe(m, initialValue):
    def extractReturnValue(f):
        f.trap(pipe.ReturnValue)
        try:
            f.raiseException()
        except pip.ReturnValue, retv:
            return retv.ret
        
    return m(initialValue).addErrback(extractReturnValue)

def pipe(fs):
    def _(v):
        return defer_utils.fold(lambda a, f : f(a), v, fs)

    return _


def compose(fs):
    fs = list(fs)
    fs.reverse()
    return pipe(fs)


returnValue = pipe.returnValue
