import hashlib

from igs.utils import config

class Error(Exception):
    pass

class AuthTokenError(Error):
    """
    Auth tokens do not match
    """
    pass

def generateToken(machineConf):
    """
    NOT REALLY SECURE OR ANYTHING

    Just takes the private key file, hashes it
    then returns the digest to be used as a token
    to do some minor authentication between clusters

    This returns a sha256 of the private key file, which
    could be a security risk in theory, I guess
    """
    fin = open(machineConf('cluster.cluster_private_key'))
    data = ''.join([l.strip()
                    for l in fin])
    return hashlib.sha256(data).hexdigest()
