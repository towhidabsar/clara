'''
Common utilities used accross modules
'''

# Python imports
import sys


class UnknownLanguage(Exception):
    '''
    Signals use of unknown language either in parser or interpreter.
    '''


DEBUG_DEST = sys.stderr
ERROR_DEST = sys.stderr


def debug(msg, *args):
    if args:
        msg %= tuple(args)
    print >> DEBUG_DEST, '[debug] %s' % (msg,)


def error(msg, *args):
    if args:
        msg %= tuple(args)
    print >> ERROR_DEST, '[error] %s' % (msg,)


def get_option(cf, section, option, default=None):
    '''
    Safe option getter with default value
    '''

    if cf.has_option(section, option):
        return cf.get(section, option)
    else:
        return default


def get_int_option(cf, section, option, default=None):
    '''
    Safe (int) option getter with default value
    '''

    if cf.has_option(section, option):
        return cf.getint(section, option)
    else:
        return default


def get_bool_option(cf, section, option, default=None):
    '''
    Safe (bool) option getter with default value
    '''

    if cf.has_option(section, option):
        return cf.getboolean(section, option)
    else:
        return default


def parseargs(argvs):
    '''
    Simple argument parser
    '''

    args = []
    kwargs = {}

    nextopt = None

    for arg in argvs:
        if nextopt:
            kwargs[nextopt] = arg
            nextopt = None

        elif arg.startswith('--'):
            nextopt = arg[2:]

        elif arg.startswith('-'):
            kwargs[arg[1:]] = True

        else:
            args.append(arg)

    return args, kwargs


def cleanstr(s):
    '''
    Strips \n\r\t from a string
    Changes \n\r\t to literals
    '''

    s = s.strip(' \t\r\n\\t\\r\\n')
    s = s.replace('\r\n', '\\n')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')

    return s
