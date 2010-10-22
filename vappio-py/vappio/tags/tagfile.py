##
# Contains functions for dealing with tag files
import os
import json

from igs.utils.config import configFromMap, configFromStream, configToDict
from igs.utils.commands import runSystemEx, runSingleProgramEx
from igs.utils import functional as func


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

def ungzFile(fname):
    runSingleProgramEx('gzip -dc %s > %s' % (fname, fname[:-3]))
    return fname[:-3]

                       
def isArchive(fname):
    """
    Returns true if fname ends in:
    .tar.bz2
    .tar.gz
    .tgz
    .gz
    """
    return any([fname.endswith(i) for i in ['.tar.bz2', '.tar.gz', '.tgz', '.gz']])

def expandArchive(fname):
    """
    This expands an archive in the directory the archive lives in and returns the sequence of file names
    """
    if fname.endswith('.tar.gz') or fname.endswith('.tgz'):
        return untargzFile(fname)
    elif fname.endswith('.gz'):
        return ungzFile(fname)
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
        else:
            raise IOError('%s does not exist' % f)
                

def partitionFiles(files, baseDir):
    if baseDir:
        baseDirFiles = [f.replace(baseDir, '')
                        for f in files
                        if f.startswith(baseDir)]
        downloadFiles = [f
                         for f in files
                         if not f.startswith(baseDir)]
        return (baseDirFiles, downloadFiles)
    else:
        return ([], files)
    

def removeBase(baseDir, f):
    if baseDir[-1] != '/':
        baseDir += '/'

    if f.startswith(baseDir):
        return f.replace(baseDir, '', 1)

    return f
    
def tagData(tagsDir, tagName, tagBaseDir, files, recursive, expand, compress, append, overwrite, metadata=None, filterF=None):
    """
    Tag a list of files with the name.  The files can contain direcotires, and if recursive
    is set the contends of the directories will become part of the tag rather than just the name

    tagBaseDir is the name of the directory that is not part of the actual tag heirarchy
    
    expand will cause any archives listed to be expanded and the contents of the archive to be added

    compress will compress the files that have been put in the tag.  compress should be the path to the
    directory the compressed file should be put.

    append will add to a tagName if it already exists, only unique names will be kept though

    filterF - if you want to filter any of the files as they are added to the file list provide a filter
    function that will be called on each individual file name.  The file will be added if filter returns True

    This returns the tag that was created
    """

    if metadata is None:
        metadata = {}
        
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


    files = [f
             for f in generateFileList(files, recursive, expand)
             if f not in oldFiles and (not filterF or filterF and filterF(f))]
        

    if overwrite:
        ##
        # If we are just overwritign the file, no need to old the list of oldFiles
        # Technically it shouldn't matter but if the old file list is really large
        # the lookup could be expensive
        outFile = open(outName, 'w')
        oldFiles = set()
    else:
        outFile = open(outName, 'a')

    
    outFile.write('\n'.join(files))
    outFile.write('\n')
    outFile.close()

    #
    # If we are compressing the files then, load the tag back up
    # so we have all of the files there
    if compress:
        outTar = str(os.path.join(compress, tagName + '.tar'))
        outGzip = outTar + '.gz'
        if not append and os.path.exists(outGzip):
            os.remove(outGzip)
        runSystemEx('mkdir -p ' + compress)
        files = loadTagFile(outName)('files')
        baseDirFiles, nonBaseDirFiles = partitionFiles(files, tagBaseDir)
        if baseDirFiles:
            for fs in func.chunk(100, baseDirFiles):
                cmd = ['tar',
                       '-C', tagBaseDir,
                       '-rf', outTar,
                       ]
                cmd.extend([removeBase(tagBaseDir, f) for f in fs])
                runSystemEx(' '.join(cmd), log=True)

        if nonBaseDirFiles:
            for fs in func.chunk(100, nonBaseDirFiles):
                cmd = ['tar',
                       '-C', '/',
                       '-rf', outTar,
                       ]
                cmd.extend([removeBase('/', f) for f in fs])
                runSystemEx(' '.join(cmd), log=True)

        runSystemEx('gzip ' + outTar, log=True)
        metadata = func.updateDict(metadata, {'compressed': True,
                                              'compressed_file': outGzip})

    #
    # If tagBaseDir is set it means we have some metadata to write
    if tagBaseDir:
        metadata['tag_base_dir'] = tagBaseDir

    if append and os.path.exists(outName + '.metadata'):
        tmd = json.loads(open(outName + '.metadata').read())
        metadata = func.updateDict(tmd, metadata)

    outFile = open(outName + '.metadata', 'w')
    outFile.write(json.dumps(metadata, indent=1) + '\n')
    outFile.close()

    return loadTagFile(outName)
    

def runCommand(_ctype, _baseDir, command, _tagfile):
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
        phantom = configFromMap({'phantom_tag': True, 'phantom': configToDict(configFromStream(open(fname + '.phantom'), lazy=True))}, lazy=True)
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

    
def loadAllTagFiles(directory):
    def _cutExtension(f):
        if f.endswith('.metadata') or f.endswith('.phantom'):
            ##
            # Cut off the ending .(metadata|phantom)
            return '.'.join(f.split('.')[:-1])
        return f
    
    tags = set([_cutExtension(f) for f in os.listdir(directory)])
    return dict([(f, loadTagFile(os.path.join(directory, f))) for f in tags])
    
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
    phantom.  That is 'isPhantom(tag) and hasFiles(tag)' could be
    True
    """
    return tagfile('phantom_tag', default=False)

