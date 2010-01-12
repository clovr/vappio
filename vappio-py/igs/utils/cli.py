##
# Little tools to make working with the CLI easier
import optparse

from igs.utils.config import configFromStream, configFromMap, configFromEnv, replaceStr

class MissingOptionError(Exception):
    pass

class InvalidOptionError(Exception):
    pass

class CLIError(Exception):
    def __init__(self, option, original):
        self.msg = str(original)
        self.option = option

    def __str__(self):
        return 'Error handling option: %s, failed with message: %s' % (self.option, self.msg)

def buildConfigN(options, usage=None, putInGeneral=True):
    """
    This builds a config from options.  Options is a list of tuples that looks like:

    (name, short, long, help, func, [bool])
    Where
    name - Name of the option, this is what it will become in the config file
    short - Short option - needs to start with -
    long - Long option - needs to start with --
    help - Help to be given to a user in --help output
    func - Function to be applied to the value
    bool - This is not required, set to True if the option is simply a boolean, all other datatypes can be verified via 'func'

    This will implicitly check if a 'conf' option exists, and if so load te conf file as a base for these config options.

    All options are put into the 'general' section.

    This returns a tuple
    (conf, args)
    where args is whatever is left over from parsing

    This also implicitly loads the current environment into the env section
    """
    def _iterBool(v):
        """
        Adds the non erquired bool field with a default of False if
        it is not present
        """
        for l in v:
            if len(l) == 6:
                yield l
            else:
                yield tuple(list(l) + [False])
                
    
    parser = optparse.OptionParser(usage=usage)

    ##
    # keep track of the function to apply to conf
    confFunc = None
    
    for n, s, l, h, f, b in _iterBool(options):
        if n == 'conf':
            confFunc = f
            
        if b:
            parser.add_option(s, l, dest=n, help=h, action='store_true')
        else:
            parser.add_option(s, l, dest=n, help=h)

    ops, args = parser.parse_args()

    baseConf = configFromEnv()
    if hasattr(ops, 'conf'):
        baseConf = configFromStream(open(confFunc(ops.conf)), baseConf)

    vals = {}

    for n, _s, l, _h, f, _b in _iterBool(options):
        try:
            ##
            # We want to apply any replacements on the options
            # The question is if baseConf is really the config file
            # we should be applying these from...
            v = f(getattr(ops, n))
            try:
                vals[n] = replaceStr(v, baseConf)
            except TypeError:
                vals[n] = v
        except Exception, err:
            raise CLIError(l, err)
            

    if putInGeneral:
        vals = {'general': vals}
    return (configFromMap(vals, baseConf), args)



##
# These are various functions to make building and verifying data easier
def notNone(v):
    """
    Throws MissingOptionError if v is None, otherwise returns v
    """
    if v is None:
        raise MissingOptionError('Must provide a value for option')

    return v


def defaultIfNone(d):
    """
    Returns a function that returns the value 'd' if the passed
    value to the function is None
    """
    def _(v):
        if v is None:
            return d
        else:
            return v

    return _

def restrictValues(values):
    def _(v):
        if v not in values:
            raise InvalidOptionError('Value must be one of: %s' % ', '.join([str(x) for x in values]))
        return v

    return _
