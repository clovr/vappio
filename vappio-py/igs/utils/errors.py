##
# Various exceptions/errors can be defined here

class TryError(Exception):
    """
    Used when you want to try something but it fails but you want to return
    a partial result.  

    .result contains this result
    .msg contains whatever message the caller put in there
    """
    def __init__(self, msg, result):
        self.msg = msg
        self.result = result

    def __str__(self):
        return str(self.msg)

