import hashlib

from twisted.python import log

from igs.utils import config

class Error(Exception):
    pass

class AuthTokenError(Error):
    """
    Auth tokens do not match
    """
    pass

def _parsePubKeyLine(line):
    """
    Parses out key portion of RSA public key i.e.

    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQE.... ==test.clovr.org OR
    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQE.... = test.clovr.org
   
    Will return ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQE....

    """
    log.msg('DEBUG auth_token #1:', line)

    line = line.strip()
    if line and '==' in line:
        (key, ident) = line.split('==')
    elif line: 
        (key, ident) = line.rsplit(' ', 1)

    log.msg('DEBUG parsed pub line:', key)

    return key        

def generateToken(keyFile):
    """
    NOT REALLY SECURE OR ANYTHING.

    Takes a public rsa key, hashes it then returns the digest to be used as a 
    token to do some minor authentication between clusters.
    
    """
    log.msg('DEBUG auth_token #2:', keyFile)

    fin = open(keyFile)
    data = ''.join([_parsePubKeyLine(line) for line in fin])
    return hashlib.sha256(data).hexdigest()

def validateToken(token):
    """
    Validates an authentication token by checking whether or not it exists 
    in the authorized_keys file. 
    
    """
    # Probably don't want to hardcore path to authorized_keys file here
    authorizedKeys = [_parsePubKeyLine(line) for line in 
                      open('/home/www-data/.ssh/authorized_keys') if line.strip()]

    authorizedTokens = [hashlib.sha256(x).hexdigest() for x in authorizedKeys]

    return token in authorizedTokens
