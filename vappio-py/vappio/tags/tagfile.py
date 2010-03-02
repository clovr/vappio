##
# Contains functions for dealing with tag files
import os

from igs.utils.commands import runSystemEx, runSingleProgramEx


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
                yield i
        elif recursive and os.path.isdir(f):
            for i in generateFileList([os.path.join(f, fn) for fn in os.listdir(f)],
                                      recursive,
                                      expand):
                yield i
        else:
            yield f
                

def tagData(tagsDir, tagName, files, recursive, expand, append, overwrite, filterF=None):
    """
    Tag a list of files with the name.  The files can contain direcotires, and if recursive
    is set the contends of the directories will become part of the tag rather than just the name

    expand will cause any archives listed to be expanded and the contents of the archive to be added

    append will add to a tagName if it already exists, only unique names will be kept though

    filterF - if you want to filter any of the files as they are added to the file list provide a filter
    function that will be called on each individual file name.  The file will be added if filter returns True
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

    for f in generateFileList(files, recursive, expand):
        if f not in oldFiles:
            if not filterF or filterF and filterF(f):
                outFile.write(f + '\n')

    outFile.close()
    
