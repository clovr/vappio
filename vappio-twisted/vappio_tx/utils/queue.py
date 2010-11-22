
RANDOM_QUEUE_STATE = 0

def randomQueueName(baseName):
    # Evil I know, storing state like this
    global RANDOM_QUEUE_STATE
    # The 10000 is arbitrary here
    if RANDOM_QUEUE_STATE > 10000:
        RANDOM_QUEUE_STATE = 0
    else:
        RANDOM_QUEUE_STATE += 1
    return '/queue/' + baseName + '-' + str(time.time()) + '-' + str(RANDOM_QUEUE_STATE)
