import os

GLOBAL_STATE_COUNTER = 0

def make_ref():
    global GLOBAL_STATE_COUNTER

    ret = str(os.getpid()) + '-' + str(GLOBAL_STATE_COUNTER)
    GLOBAL_STATE_COUNTER += 1

    return ret

