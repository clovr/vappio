##
# These define useful policies for ensuring a machine is configed properly.  This should probably be off lifted into
# a program/library designed for this, but what I need right now is simple
import os

from igs.utils.logging import errorPrint
from igs.utils.commands import runSingleProgram, ProgramRunError
from igs.utils.config import configFromMap, configFromStream, replaceStr


##
# These are default config options, these will be moved to a config file eventually
conf = configFromMap({
    'stow': {'dir': '/usr/local/stow'},
    'base': {'dir': '/usr/local'},
    'config': {'filename': '/tmp/machine.conf'}
    })



##
# Exceptions
class PolicyError(Exception):
    pass


##
# A little helper function
def runSystemEx(cmd):
    """This just ignores all stdout"""
    code = runSingleProgram(cmd, None, errorPrint)
    if code != 0:
        raise ProgramRunError(cmd, code)



def runInDir(dir, f):
    """Helper function, wraps calling f in a specific directory"""
    curdir = os.getcwd()
    os.chdir(dir)
    f()
    os.chdir(curdir)

def dirExists(dirname):
    """
    Ensure a directory exists, create it if not
    Use fileExists if you want to check for existence but not create
    """
    dirname = replaceStr(dirname, conf)
    if not os.path.exists(dirname):
        try:
            runSystemEx('mkdir -p ' + dirname)
        except:
            raise PolicyError('Could not create directory: ' + dirname)

def fileExists(fname):
    fname = replaceStr(fname, conf)
    if not os.path.exists(fname):
        raise PolicyError('File does not exist: ' + fname)
        
def fileOwner(fname, owner, group=None):
    fname = replaceStr(fname, conf)
    who = owner
    if group:
        who += ':' + group

    runSystemEx('chown %s %s' % (who, fname))
        
def dirOwner(dirname, owner, group=None):
    """Set owners of a directory, recursively. use fileOwner if you do not want recursive"""
    dirname = replaceStr(dirname, conf)
    who = owner
    if group:
        who += ':' + group

    runSystemEx('chown -R %s %s' % (who, dirname))


def ensurePkg(pkgname):
    """Ensure's a package exists"""
    path = os.path.join(conf('stow.dir'), pkgname)
    if not os.path.exists(path):
        raise PolicyError('Package does not exist: ' + path)


def installPkg(pkgname):
    runInDir(conf('stow.dir'),
             lambda : runSystemEx('xstow ' + pkgname))

def uninstallPkg(pkgname):
    runInDir(conf('stow.dir'),
             lambda : runSystemEx('xstow -D ' + pkgname))    


def pkgFileExists(pkgname, fname):
    """Ensures a file in the package exists"""
    fname = replaceStr(fname, conf)
    fileExists(os.path.join(conf('stow.dir'), pkgname, fname))
    

def run(cmd):
    """This runs a command, be sure that the command backgrounds, add & if you need to"""
    runSystemEx(replaceStr(cmd, conf))
    

def executeTemplate(fname):
    """
    Executes a template, at this point this is simple variable substitution in a file
    but it could grow to be more complicated.

    This takes a file that ends in .tmpl and produces a file without the .tmpl with the template
    executed
    """
    fname = replaceStr(fname, conf)
    if not fname.endswith('.tmpl'):
        raise PolicyError('%s does not end in .tmpl' % fname)

    fout = open(fname[:-5], 'w')
    fin = open(fname)

    configFile = configFromStream(open(conf('config.filename')))
    
    for line in fin:
        fout.write(replaceStr(line, configFile))

    fout.close()
    fin.close()


def executePkgTemplate(pkgname, fname):
    """Just a handy wrapper for executing templates in a specific package"""
    executeTemplate(os.path.join(conf('stow.dir'), pkgname, fname))
    
