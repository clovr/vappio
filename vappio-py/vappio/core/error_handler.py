##
# Useful functions for handling errors since all of this happens asynchronously and the
# db is or only place for
import time

import pymongo

from igs.utils import errors as errorutils


def runCatchError(func, fail):
    """
    This runs a function and catches any exceptions thrown and calls the fail
    function if an error is thrown with the caught exception

    It returns True on success and False on error
    """
    try:
        func()
    except Exception, err:
        fail(err)
        raise


def mongoFail(runInfo):
    """
    This returns a functiont aht can be used in runCatchError.  runInfo is a dict
    of the information that should be put in the errors collection.

    A timestamp and error_msg key will be added to the dict upon insertion
    """
    def _(err):
        errors = pymongo.Connection().clovr.errors
        runInfo['error_msg'] = str(err)
        runInfo['timestamp'] = int(time.time())
        runInfo['stacktrace'] = errorutils.getStacktrace()
        errors.insert(runInfo)

    return _
