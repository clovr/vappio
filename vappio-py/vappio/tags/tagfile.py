##
# Contains functions for dealing with tag files
import os

from igs.utils.commands import runSystemEx

def isArchive(fname):
    """
    Returns true if fname ends in:
    .bz2
    .tar.gz
    .tgz
    """
    return False

def expandArchive(fname):
    """
    This expands an archive in the directory the archive lives in and returns the sequence of file names
    """
    raise Exception('Not implemented yet')

def generateFileList(files, recursive, expand):
    """
    Takes a list of files and walks over them generating
    a stream of file names.
    """
    for f in files:
        if expand and isArchive(f):
            for i in expandArchive():
                yield i
        elif recursive and os.path.isdir(f):
            for i in generateFileList([os.path.join(f, fn) for fn in os.listdir(f)],
                                      recursive,
                                      expand):
                yield i
        else:
            yield f
                

def tagFiles(tagsDir, tagName, files, recursive, expand, append, overwrite, filterF=None):
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
    
