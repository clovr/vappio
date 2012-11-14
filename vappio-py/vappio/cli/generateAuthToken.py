#!/usr/bin/env python

##
# Generates an authorization token for cluster communication given a file
import sys

from igs.utils import auth_token

key_file = sys.argv[1]

if not key_file:
    raise Exception('Must supply key file')

print auth_token.generateToken(key_file)
