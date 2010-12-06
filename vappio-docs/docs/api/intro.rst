Introduction
============

What is the vappio API?
-----------------------

``vappio`` is an API for the creation and manipulation of clusters on a cloud in a platform 
agnostic way.  ``vappio`` was originally designed on top of EC2 so in some places it uses EC2 
terminology but the functionality is more generic.  As of this writing (Dec 6 2010) ``vappio`` 
works on EC2 and Nimbus based infrastructures.

This document provides the description of the API that a ``vappio`` implementation is expected
to adhere.  A command line and webservice based API is shown.

The command line API
--------------------

The description of the command line tools detail the differences between them.  Most of the tools
share some functionality described here.

--host and --name
^^^^^^^^^^^^^^^^^

Almost all command line programs take a ``--host`` and ``--name`` option.  Because the command line
API is using the webservices in the background the host to connect to can be specified with
``--host``.  In many cases one wishes to specify a particular cluster to run a command on.  For example
if one has an EC2 cluster up and wants to add instances they would want to specify which cluster to
add instances to.  This is done through the ``--name`` option.  These values default to ``localhost``
and ``local`` respectively.  

--print-task-name
^^^^^^^^^^^^^^^^^

Some of the command line tools create long running processes.  A single webservice request would timeout
if it waited for a response.  To get around this ``vappio`` has the concept of a ``task``.  A ``task``
is an identifier for that can be used with the tasks API to query the states of a long running process.
By default the command line tools will block until a ``task`` is completed or failed.  One can use
``--print-task-name`` to print out the name of the task rather than block on it and use it later, perhaps
with ``vp-describe-task``.  This allows the command line tools to be used asynchronously if needed.


The webservice API
------------------

All of the webservices use ``JSON`` as the language for communication.  The documentation of the webservices 
include valid ``JSON`` input and the expected responses.  Many of the webservice operations actually initiate 
long running jobs in which case a task id (which is a string) is returned.  This task id can be queried using 
the tasks webservice API. Other webservices return more complicated data structures.  The response from a 
webservice is always wrapped in a ``JSON`` dictionary that describes if the operation was a success or failure.

Response objects
^^^^^^^^^^^^^^^^

All ``vappio`` webservice responses are a dictionary with the following attributes:

=========  =======  ======================================================================================================================================= 
Parameter  Type     Meaning
=========  =======  =======================================================================================================================================
success    Boolean  If true, the request was successfull and the ``data`` attribute contains the response.  If false ``data`` contains failure information.
data       Any      On success this is whatever the API documentation describes the output to be.  On failure it is an ``error`` object described below.
=========  =======  ======================================================================================================================================= 

An ``error`` object:

==========  ======  ========================================================================
Parameter   Type    Meaning
==========  ======  ========================================================================
msg         String  A message describing the error.
name        String  The type or name of the error.  This could be empty.
stacktrace  String  A stacktrace of the error if it can be determined.  This could be empty.
==========  ======  ========================================================================


Here is an example successful output from the ``list clusters`` API: ::

    {
     "data": [
      "local", 
      "diag-3", 
      "diag-2", 
      "diag-1"
     ], 
     "success": true
    }


Here is an example failure output from the ``describe clusters`` API: ::

    {
     "data": {
      "msg": "anycluster", 
      "stacktrace": "Traceback (most recent call last):\n  File \"/opt/vappio-py/igs/cgi/handler.py\", line 56, in generatePage\n
    body = cgiPage.body()\n  File \"/var/www/vappio/clusterInfo_ws.py\", line 31, in body\n
    cluster = cluster_ctl.loadCluster(request['name'])\n  File \"/opt/vappio-py/vappio/cluster/control.py\", line 237, in loadCluster\n
    cl = persist_mongo.load(name)\n  File \"/opt/vappio-py/vappio/cluster/persist_mongo.py\", line 55, in load\n
    raise ClusterDoesNotExist(name)\nClusterDoesNotExist: anycluster\n", 
      "name": "vappio.cluster.persist_mongo.ClusterDoesNotExist"
     }, 
     "success": false
    }
