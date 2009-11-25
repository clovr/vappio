##
# This is for working with ini style configs.  This offers a few tricks though:
#
# 1) You can reference variables in this by ${vname}
#    For example you can have:
#    foo = bar
#    bar = baz
#    foobar = ${foo}${bar}
#    And foobar will be barbaz
# 2) The name of a section is really just a short hand for writing fully dot separated names out. For example:
#    [general]
#    bar = baz
#    foo = zoom
#
#    This is really equivalent to:
#    []
#    general.bar = baz
#    general.foo = zoom
#
#    Note the [] at the top says we went the root section.  This means you can access variables as: ${general.bar} if you want to access it in another section.
#    Names in a particular section are searched in that section and then search the root name.  For example:
#    []
#    foo = bar
#    [general]
#    baz = zoom
#    t1 = ${baz}
#    t2 = ${foo}
#
#    t1 is zoom, t2 is bar
# 3) You can also add to sections defined elsewhere in the file (although not suggested).  For example:
#    [general]
#    foo = bar
#    [other]
#    test = testing
#    [general]
#    bar = baz
#
#    This is equivalent to moving appending the second general to the first, HOWEVER.
import re

##
# Regex to find variables in a string so we can replace on them
VARIABLE_RE = re.compile(r'\${([A-Za-z0-9_\.]+)}')

class ConfigParseError(Exception):
    pass

class NoKeyFoundError(Exception):
    def __init__(self, k):
        self.key = k

    def __str__(self):
        return self.key

def configToFun(conf):
    def _(k, *args, **kwargs):
        try:
            return conf[k]
        except KeyError:
            if args:
                return args[0]
            elif 'default' in kwargs:
                return kwargs['default']
            else:
                raise NoKeyFoundError(k)

    return _

def chainConfigFuns(cfs):
    def _(k, *args, **kwargs):
        for c in cfs:
            try:
                return c(k)
            except NoKeyFoundError:
                pass

        if args:
            return args[0]
        elif 'default' in kwargs:
            return kwargs['default']
        else:
            raise NoKeyFoundError(k)

    return _


def configFromStream(stream, base=None):
    """
    Constructs a config function from a stream.

    base is used if you want to make this on top of base (for example this references variables in base.

    The returned value will be a composite of base with stream."""

    ##
    # We are just going to read the config file into a map and use configFromMap
    cfg = {'': {}}
    ##
    # Default section
    section = ''
    for line in stream:
        line = line.lstrip()
        if not line or line[0] == '#':
            # A comment or empty line
            continue

        if line[0] == '[':
            line = line.rstrip()
            if line[-1] == ']':
                section = line[1:-1]
                if section not in cfg:
                    cfg[section] = {}
                continue
            else:
                raise ConfigParseError("""Error parsing line: %r""" % line)
        else:
            key, value = line.split('=', 1)
            ##
            # Remove the trailing '\n'
            cfg[section][key] = value[:-1]

    return configFromMap(cfg, base)

        


def flattenMap(map):
    res = {}
    for k, v in map.iteritems():
        if k:
            n = k + '.'
        else:
            n = ''
        ##
        # Cheap way to see if v is a map
        if hasattr(v, 'keys'):
            for kp, vp in flattenMap(v).iteritems():
                res[n + kp] = vp
        else:
            res[k] = v

    return res

def replaceVariables(k, value, lookup):
    """
    Takes value and determines if any variables need replacing in it and replaces
    them with whatever is in 'lookup'.  This will blow out the stack if
    you have a recursive variables.

    If a variable cannot be found a NoKeyFoundError is thrown.
    """
    ##
    # We want the section for this variable which means if the key is
    # a.b.c.d the section is a.b.c
    # If the key is empty, the section is empty
    if '.' in k:
        ##
        # Add trailing . so we don't have to later
        section = '.'.join(k.split('.')[:-1]) + '.'
    else:
        section = ''

    ##
    # Check to make sure this is a string:
    if hasattr(value, 'replace'):
        vars = VARIABLE_RE.findall(value)
        if vars:
            for var in vars:
                if '.' not in var:
                    secVar = section + var
                else:
                    secVar = var

                value = value.replace('${%s}' % var, lookup(secVar))

            return replaceVariables(k, value, lookup)
        else:
            return value
    else:
        return value


def replaceStr(str, lookup):
    """Takes a string and replaces all variables in it with values from config"""
    vars = VARIABLE_RE.findall(str)
    if vars:
        for var in vars:
            str = str.replace('${%s}' % var, lookup(var))

    return str

    
        

def configFromMap(map, base=None):
    """
    Constructs a config function from a map.  Values can be any type however
    if they are a string they will be processed for variable substitution.

    base is used if you want to make this on top of base (for example this references variables in base.

    The returned value will be a composite of base with stream.    
    """

    ##
    # First, flatten it:
    conf = flattenMap(map)

    if base:
        chained = chainConfigFuns([configToFun(conf), base])
    else:
        chained = configToFun(conf)

    for k in conf.keys():
        v = conf[k]
        newV = replaceVariables(k, v, chained)
        if newV != v:
            conf[k] = newV


    return chained

            

def test():
    c = configFromMap({
        'general': {'foo': '${bar}',
                    'bar': 'baz'},
        'test': {'foo': '${general.foo}',
                 'bar': '${zoom}',
                 'zoom': 'bye'},
        })

    print c('general.foo')
    print c('general.bar')
    print c('test.foo')
    print c('test.bar')
    print c('test.zoom')


    c1 = configFromMap({
        'general': {'zoom': '${bar}'},
        'testing': {'zoom': '${test.zoom}'}
        }, c)

    print c1('general.zoom')
    print c1('testing.zoom')
    
    
