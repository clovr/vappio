##
# Contains functions for dealing with tag files
import os
import json

from igs.utils.config import configFromMap, configFromStream, configToDict
from igs.utils.commands import runSystemEx, runSingleProgramEx


class MissingTagFileError(Exception):
    pass

def untargzFile(fname):
    stdout = []
    runSingleProgramEx('tar -C %s -zxvf %s' % (os.path.dirname(fname), fname), stdout.append, None)
    return (os.path.join(os.path.dirname(fname), i.strip()) for i in stdout)


def bunzip2File(fname):
    stdout = []
    runSingleProgramEx('bzcat %s | tar -C %s -xv' % (fname, os.path.dirname(fname)), stdout.append, None)
    return (os.path.join(os.path.dirname(fname), i.strip()) for i in stdout)

                       
def isArchive(fname):
    """
    Returns true if fname ends in:
    .tar.bz2
    .tar.gz
    .tgz
    """
    return any([fname.endswith(i) for i in ['.tar.bz2', '.tar.gz', '.tgz']])

def expandArchive(fname):
    """
    This expands an archive in the directory the archive lives in and returns the sequence of file names
    """
    if fname.endswith('.tar.gz') or fname.endswith('.tgz'):
        return untargzFile(fname)
    elif fname.endswith('.tar.bz2'):
        return bunzip2File(fname)
    

def generateFileList(files, recursive, expand):
    """
    Takes a list of files and walks over them generating
    a stream of file names.
    """
    for f in files:
        if expand and isArchive(f):
            for i in expandArchive(f):
                if os.path.isfile(i):
                    yield i
        elif recursive and os.path.isdir(f):
            for i in generateFileList([os.path.join(f, fn) for fn in os.listdir(f)],
                                      recursive,
                                      expand):
                yield i
        elif os.path.isfile(f):
            yield f
                

def tagData(tagsDir, tagName, tagBaseDir, files, recursive, expand, append, overwrite, filterF=None):
    """
    Tag a list of files with the name.  The files can contain direcotires, and if recursive
    is set the contends of the directories will become part of the tag rather than just the name

    tagBaseDir is the name of the directory that is not part of the actual tag heirarchy
    
    expand will cause any archives listed to be expanded and the contents of the archive to be added

    append will add to a tagName if it already exists, only unique names will be kept though

    filterF - if you want to filter any of the files as they are added to the file list provide a filter
    function that will be called on each individual file name.  The file will be added if filter returns True

    This returns the tag that was created
    """
    if not os.path.exists(tagsDir):
        runSystemEx('mkdir -p ' + tagsDir)
    
    outName = os.path.join(tagsDir, tagName)
    if os.path.exists(outName) and not append and not overwrite:
        raise Exception('Tag already exists')


    ##
    # Keep a set of all old entries in the file, when we walk the generator we'll
    # we'll check to see if the file already exists in here
    if append and os.path.exists(outName):
        oldFiles = set([l.strip() for l in open(outName)])
    else:
        oldFiles = set()

    if overwrite:
        ##
        # If we are just overwritign the file, no need to old the list of oldFiles
        # Technically it shouldn't matter but if the old file list is really large
        # the lookup could be expensive
        outFile = open(outName, 'w')
        oldFiles = set()
    else:
        outFile = open(outName, 'a')



    files = [f for f in generateFileList(files, recursive, expand)
             if f not in oldFiles and (not filterF or filterF and filterF(f))]
        

    outFile.write('\n'.join(files))
    outFile.write('\n')
    outFile.close()

    ##
    # If tagBaseDir is set it means we have some metadata to write
    if tagBaseDir:
        outFile = open(outName + '.metadata', 'w')
        outFile.write(json.dumps(dict(tag_base_dir=tagBaseDir)))
        outFile.close()

    return loadTagFile(outName)
    

def runCommand(ctype, baseDir, command, tagfile):
    runSystemEx(command)
    

def realizePhantom(ctype, baseDir, tagfile):
    """
    This takes a phantom tag and turns it into
    a real tag (creating/downloading the files)
    
    ctype - The current cluster type, this says which cluster.$ctype to look at
    baseDir - The base directory to download the files to
    tagfile - The tag file.

    In the tag, ctype and baseDir can be referenced through ${ctype} and ${base_dir}
    """
    newTag = configFromMap({'ctype': ctype,
                            'base_dir': baseDir},
                           tagfile)

    ##
    # Get what to download, first try the url then get the command if it is not there.
    # We define a url as anything that starts with <protocol_we_understand>://
    # so if it doesn't match that, it's a command and we run that
    download = newTag('phantom.cluster.%s.url' % ctype, default=newTag('phantom.cluster.%s.command' % ctype))

    if download.startswith('http://'):
        #downloadHttp(ctype, baseDir, download, tagfile)
        pass
    elif download.startswith('s3://'):
        ##
        # We might ened to modify realizePhantom to take a conf that will have our s3 credentails in it
        #downloadS3(ctype, baseDir, download, tagfile)
        pass
    else:
        ##
        # It's a command:
        runCommand(ctype, baseDir, download, tagfile)


def loadTagFile(fname):
    """
    Loads a tagfile, returns a config object of attributes

    Also considering a .phantom type which would represent files that don't really exist.  I think this makes sense
    as you should be able to tarnsfer .phantom files around but .metadata's should be generated when you make a tag

    Will explain more abou this in a wiki page somewhere...
    """
    ##
    # Phantom filse are in a format that configFromStream can read.  This is because phantom files
    # are expected to be written and modified by humans.  .metadata files on the other hand
    # are just expected to be the produce of a machine storing information so uses json
    if os.path.exists(fname + '.phantom'):
        ##
        # Put everythin under phantom
        # We want to do it lazily too since we will be adding
        # data it can access later
        phantom = configFromMap({'phantom': configToDict(configFromStream(open(fname + '.phantom'), lazy=True))}, lazy=True)
    else:
        phantom = configFromMap({})

    ##
    # If the fname actually exists, open its meta data + files
    # if the fname does not exist but the phantom does, return the phantom
    # otherwise, throw an exception about missing the tagfile
    if os.path.exists(fname):
        if os.path.exists(fname + '.metadata'):
            metadata = configFromMap({'metadata': json.loads(open(fname + '.metadata').read())}, phantom)
        else:
            metadata = configFromMap({}, phantom)

        return configFromMap({'files': [f.strip() for f in open(fname) if f.strip()]}, metadata)
    elif not os.path.exists(fname) and os.path.exists(fname + '.phantom'):
        return phantom
    else:
        raise MissingTagFileError(fname)

    
    
def hasFiles(tagfile):
    """
    Returns true if this tagfile contains files
    This, at the very least, means it's a realized phantom
    """
    return 'files' in tagfile.keys()


def isPhantom(tagfile):
    """
    Returns true if this tagfile contains phantom file information.
    Being a phantom is not mutually exclusive with beinga 'realized'
    phantom.  That is 'isPhantom(tag) and hasRealFiles(tag)' could be
    True
    """
    for k in tagfile.keys():
        if k.startswith('phantom.'):
            return True

    return False

