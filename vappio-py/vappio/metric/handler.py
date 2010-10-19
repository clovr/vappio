import sys

CAT = lambda s k v: s.write('='.join([k, v]) + '\n')


class InvalidHeader(Exception):
    pass

class MissingRequiredKeys(Exception):
    pass

def runMetric(inHeader,
              outHeader,
              inStream=sys.stdin,
              outStream=sys.stdout,
              requiredKeys=None,
              optionalKeys=None,
              preFunc=None,
              postFunc=None,
              streamFunc=None):
    header = inStream.readline().strip()
    if header != inHeader:
        raise InvalidHeader('Input header %r did not match epected header %r' % (header, inHeader))

    outStream.write(outHeader + '\n')

    requiredKeys = set(requiredKeys)
    optionalKeys = set(optionalKeys)

    allKeys = requiredKeys + optionalKeys
    
    kv = {}

    for line in inStream:
        sline = line.strip()
        key, value = line.split('=', 1)

        if streamFunc:
            streamFunc(s, key, value)
            
        if key in allKeys:
            kv[key] = value

    keys = set(kv.keys())

    mKey = requiredKeys - keys
    if mKeys:
        raise MissingRequiredKeys('Missing the following required keys: ' + ' '.join(mKeys))

    
