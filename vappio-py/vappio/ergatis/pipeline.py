##
# Functions to control a pipeline running on Ergatis somewhere
import os
import sets
import time
import urllib
import httplib

from igs.utils.core import getStrBetween

PIPELINES_BUILDING='/tmp/pipelines_building'


def newPipelineFromTemplate(host, repoRoot, workflowDocs, templateDir):
    """
    Builds a new pipeline given the following information.  Returns the newly built pipeline's id
    """
    #buildDir = buildPipeline(host, repoRoot, templateDir)
    
    params = urllib.urlencode(dict(repository_root=repoRoot,
                                   workflowdocs_dir=workflowDocs,
                                   build_directory='/tmp/blastn_tmpl',
                                   skip_run=1,
                                   skip_instantiation=1,
                                   instantiate=0,
                                   builder_animations=0,
                                   autoload_template=templateDir))

    print params
    
    headers = {}
    conn = httplib.HTTPConnection(host + ':80')
    conn.request('POST', '/ergatis/cgi/run_pipeline.cgi', params, headers)

    return conn



def buildPipeline(host, repoRoot, templateDir):
    """
    Builds a pipeline and returns the build dir

    """

    params = urllib.urlencode(dict(autoload_template=templateDir,
                                   repository_root=repoRoot))
    headers = {}
    conn = httplib.HTTPConnection(host + ':80')
    conn.request('GET', '/ergatis/cgi/build_pipeline.cgi?' + params, headers=headers)

    ##
    # Probably not necessary, i think .request makes the entire call
    response = conn.getresponse()
    data = response.read()

    conn.close()

    buildDir = getStrBetween(data, "input name='build_directory' id='build_directory' value='", "'")

    return buildDir

