##
# Little tools to make working with the CLI easier


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
