##
# Misc functions related to dealing with instances

def getInstances(f, ctype):
    """
    Gets all instances that match the f predicate.
    ctype is the cluster type (a module generally)
    """
    return [i for i in ctype.listInstances() if f(i)]
