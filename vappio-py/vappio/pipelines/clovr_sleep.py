##
# THIS SHOULD BE RUN ON THE REMOTE SIDE
#
# Need to know where the template lives
TEMPLATE_NAME = 'clovr_sleep'

OPTIONS = [
    # ensure it is an int
    ('input.TIME', '', '--TIME', 'Time to sleep', int),
    ]

