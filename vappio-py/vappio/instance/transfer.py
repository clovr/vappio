##
# Useful functions for transfering files to and from a particular instance
import os
import time

from igs.utils.ssh import scpToEx, scpFromEx
from igs.utils.logging import errorPrintS
from igs.utils.commands import runSystemEx

from vappio.instance.control import runSystemInstanceEx

##
# Exeptions
class DownloadPipelineOverwriteError(Exception):
    """Really long name, I know"""
    
    def __init__(self, fname):
        self.fname = fname

    def __str__(self):
        return 'File already exists: ' + self.fname


def uploadFiles(instance, conf, srcFiles, outDir, log=False):
    """
    This uploads srcFiles to the outDir, this is very low level and meant to allow the user to upload anywhere
    instance - the instance to upload to
    conf - contains various config data, the following options need to be present:
           ssh.options - options to pass to ssh
           ssh.user - user to ssh as
    srcFiles - a list of files to upload
    outDir - the directory to put them in
    """
    ##
    # This is cheap, but we'll have the mkdir print its error out to screen if logging is on, in reality if this fails
    # we should wrap it up somehow in an exception
    runSystemInstanceEx(instance, 'mkdir -p ' + outDir, None, (log and errorPrintS or None), user=conf('ssh.user'), options=conf('ssh.options'), log=log)
    for f in srcFiles:
        scpToEx(instance.publicDNS, f, outDir, user=conf('ssh.user'), options=conf('ssh.options'), log=log)
    

def uploadTag(instance, conf, tagDir, tagName, srcFiles, outDir, log=False):
    """
    This generates a tag (file list) from srcFiles and uploads the
    tag to the tag directory.
    instance - instance to upload to
    conf - contains various config data, the following options need to be present:
           ssh.options - options to pass to ssh
           ssh.user - user to ssh as
    tagDir - directory to put the tag in
    tagName - name of the tag
    srcFiles - list of files that the tag will be generated from
    outDir - the directory the srcFiles were put into
    """
    tempFName = os.path.join('/tmp', str(time.time()))
    fout = open(tempFName, 'w')
    for f in srcFiles:
        fout.write(os.path.join(outDir, os.path.basename(f)) + '\n')

    fout.close()
    runSystemInstanceEx(instance, 'mkdir -p ' + tagDir, None, (log and errorPrintS or None), user=conf('ssh.user'), options=conf('ssh.options'), log=log)
    scpToEx(instance.publicDNS, tempFName, os.path.join(tagDir, tagName), user=conf('ssh.user'), options=conf('ssh.options'), log=log)
    os.remove(tempFName)

def uploadAndTag(instance, conf, tagName, srcFiles, outDir, log=False):
    """
    This is a high level wrapper for uploadFiles and uploadTag.  This relies on more
    data being in the conf than the other functions
    conf - contains various config data, the following options need to be present:
           ssh.options - options to pass to ssh
           ssh.user - user to ssh as
           dirs.upload_dir - directory to upload to, this is prepended to outDir
           dirs.tag_dir - directory to place tags in
    tagName - name of tag
    srcFiles - files to upload
    outDir - basename of the directory the files should go into, this will be appended to dirs.upload_dir
    """
    outDir = os.path.join(conf('dirs.upload_dir'), outDir)
    tagDir = conf('dirs.tag_dir')
    uploadFiles(instance, conf, srcFiles, outDir, log)
    uploadTag(instance, conf, tagDir, tagName, srcFiles, outDir, log)
    


def downloadPipeline(instance, conf, pipelineId, outDir, outBaseName, overwrite=False, log=False):
    """
    Downloads a pipeline from an instance.
    conf - contains various config data, the following options need to be present:
           ssh.options - options to pass to ssh
           ssh.user - user to ssh as
           dirs.clovr_project - the directory on the imave clovr project is expected to live
    pipelineId - the id of the pipeline to download
    outDir - local directory to download to
    outBaseName - The basename for the output file
    overwrite - if the downloaded file exists locally already, should it be downloaded (default No)
    """
    outF = '/mnt/%s.tar.gz' % outBaseName
    
    cmd = ['cd %s;' % conf('dirs.clovr_project'),
           'tar',
           '-zcf',
           outF,
           'output_repository/*/%s_default' % pipelineId]
    
    runSystemInstanceEx(instance, ' '.join(cmd), None, (log and errorPrintS or None), user=conf('ssh.user'), options=conf('ssh.options'), log=log)
    outFilename = os.path.join(outDir, os.path.basename(outF))
    fileExists = os.path.exists(outFilename)
    if fileExists and overwrite or not fileExists:
        runSystemEx('mkdir -p ' + outDir)
        scpFromEx(instance.publicDNS, outF, outDir, user=conf('ssh.user'), options=conf('ssh.options'), log=log)
        runSystemInstanceEx(instance, 'rm ' + outF, None, (log and errorPrintS or None), user=conf('ssh.user'), options=conf('ssh.options'), log=log)
        return outFilename
    else:
        runSystemInstanceEx(instance, 'rm ' + outF, None, (log and errorPrintS or None), user=conf('ssh.user'), options=conf('ssh.options'), log=log)        
        raise DownloadPipelineOverwriteError(outFilename)
