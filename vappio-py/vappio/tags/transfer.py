##
# Transfering tags to/from a machine
import os

from igs.utils.ssh import scpToEx, scpFromEx
from igs.utils.logging import errorPrintS, errorPrint
from igs.utils.errors import TryError
from igs.utils.commands import ProgramRunError

from vappio.tags.tagfile import loadTagFile, isPhantom

from vappio.instance.control import runSystemInstanceEx

from vappio.webservice.tag import queryTag

def makePathRelative(path):
    if path and path[0] == '/':
        return path[1:]
    else:
        return path


def makeDirsOnCluster(cluster, dirNames):
    """
    Creates a series of directories on a cluster
    """
    for d in dirNames:
        runSystemInstanceEx(cluster.master,
                            'mkdir -p ' + d,
                            None,
                            errorPrintS,
                            user=cluster.config('ssh.user'),
                            options=cluster.config('ssh.options'),
                            log=True)
        try:
            runSystemInstanceEx(cluster.master,
                                'chown -R %s %s' % (cluster.config('vappio.user'), d),
                                None,
                                errorPrintS,
                                user=cluster.config('ssh.user'),
                                options=cluster.config('ssh.options'),
                                log=True)
        except ProgramRunError, err:
            pass
            ##raise TryError('Could not chown directory', err)
    
def uploadTag(srcCluster, dstCluster, tagName, tagData):
    """
    srcCluster - Source cluster - currently this needs to be 'local'
    dstCluster - Destination cluster
    tagName - The tag to be copied, will have the same name on the destination cluster,
              must exist on srcCluster

    Tags are upload into dstCluster.config('dirs.upload_dir')

    This returns a list of file names that were uploaded
    """
    tagBaseDir = tagData('metadata.tag_base_dir', default='')
        
    
     ##
     # First step is to create a list of directorys that we should make on
     # the destination cluster.  We also want to strip off our local dirs.tag_dir
     # from the dir names and add teh dstCluster's
    dirNames = set([os.path.join(dstCluster.config('dirs.upload_dir'), tagName,
                                 makePathRelative(os.path.dirname(f).replace(tagBaseDir, '')))
                    for f in tagData('files')])


    ##
    # Next we want to take the list of local files, remove the dirs.tag_dir and replace it
    # with the destination clusters.  We maek a list of tuples so we know the local file
    # and destinatio file name which we will then loop over and upload
    dstFileNames = [(f, os.path.join(dstCluster.config('dirs.upload_dir'), tagName,
                                     makePathRelative(f.replace(tagBaseDir, ''))))
                    for f in tagData('files')]

    ##
    # Next, lets call 'mkdir -p' on all the dirs we need to make on the destination cluster
    try:
        makeDirsOnCluster(dstCluster, dirNames)
    except TryError, err:
        errorPrint('Caught TryError, ignoring for now: %s - %s ' % (err.msg, str(err.result)))

    ##
    # Now, copy up all of the files
    for l, d in dstFileNames:
        scpToEx(dstCluster.master.publicDNS, l, d, user=srcCluster.config('ssh.user'), options=srcCluster.config('ssh.options'), log=True)
        ##
        # We are uploading as root, so chown everything to the user that everything in vappio will be done under
        try:
            runSystemInstanceEx(dstCluster.master,
                                'chown %s %s' % (dstCluster.config('vappio.user'), d),
                                None,
                                errorPrintS,
                                user=dstCluster.config('ssh.user'),
                                options=dstCluster.config('ssh.options'),
                                log=True)
        except ProgramRunError:
            errorPrint('Chown failed on ' + d)
        
    ##
    # return the list of uploaded filenames
    return [d for l, d in dstFileNames]

    

def downloadTag(srcCluster, dstCluster, tagName, dstDir=None, baseDir=None):
    """
    srcCluster - Cluster to download the tag from
    dstCluster - Cluster to download the tag to (this needs to be 'local' for now)
    tagName - The name of the tag to download
    dstDir - The destination directory to put downloaded data to.  If None, dstDir
             is assumed to be dstCluster.config('dirs.upload_dir')
    baseDir - When we download a tag we replicate its directory structure, baseDir allows
              us to remove some portion of the prefix dir in downloading.  If baseDir is None
              then srcCluster.config('dirs.upload_dir') is assumed to be the baseDir

    Neither dstDir or baseDir should consider the 'tagname' as part of their name.
    This may change in the future though if we want to allow downloading to a new tag name

    TODO: Consider compressing tags on the remote side before a transfer.  It is possible it
    should be part of the download process.  Alternatively it might make more sense for the compression
    to be part of another process.
    """
    if dstDir is None:
        dstDir = os.path.join(dstCluster.config('dirs.upload_dir'), tagName)

    if baseDir is None:
        baseDir = srcCluster.config('dirs.upload_dir')

    ##
    # Get the list of files
    tagData = queryTag('localhost', srcCluster.name, tagName)

    ##
    # Create a set of directory names so we can recreate the remote structure locally
    dirNames = set([os.path.join(dstDir,
                                 makePathRelative(os.path.dirname(f).replace(baseDir, '')))
                    for f in tagData('files')])
    ##
    # Take the files and construct a list of tuples mapping the remote file name to the local file name
    lclFileNames = [(f, os.path.join(dstDir,
                                     makePathRelative(f.replace(baseDir, ''))))
                    for f in tagData('files')]

    ##
    # Make all of the directories
    try:
        makeDirsOnCluster(dstCluster, dirNames)
    except TryError, err:
        errorPrint('Caught TryError, ignoring for now: %s - %s ' (err.msg, str(err.result)))    

    ##
    # Copy the files locally
    for r, l in lclFileNames:
        scpFromEx(srcCluster.master.publicDNS, r, l, user=srcCluster.config('ssh.user'), options=srcCluster.config('ssh.options'), log=True)

    return [l for r, l in lclFileNames]
    
