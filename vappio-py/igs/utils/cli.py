##
# Little tools to make working with the CLI easier
import optparse

from igs.utils.config import configFromStream, configFromMap, configFromEnv

class MissingOptionError(Exception):
    pass


def buildConfig(parser, merger):
    """
    parser is an object that is used to parse the command line
    merger is a functiont hat is called with the results of parsing the command line

    The result is expected to be a config option
    """

    options, args = parser.parse_args()

    return merger(options, args)


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

    for n, s, l, h, _f, b in _iterBool(options):
        if b:
            parser.add_option(s, l, dest=n, help=h, action='store_true')
        else:
            parser.add_option(s, l, dest=n, help=h)

    ops, args = parser.parse_args()

    baseConf = configFromEnv()
    if hasattr(ops, 'conf'):
        baseConf = configFromStream(open(ops.conf), baseConf)

    vals = {}

    for n, _s, l, _h, f, _b in _iterBool(options):
        try:
            vals[n] = f(getattr(ops, n))
        except MissingOptionError:
            raise MissingOptionError('Failed to provide a value for option: ' + l)
            

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
        raise MissingOptionError('Must provide a value for opion')

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
