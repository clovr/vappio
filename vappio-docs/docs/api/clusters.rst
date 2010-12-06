Clusters
========

vp-start-cluster - Start a new cluster
--------------------------------------------

description
^^^^^^^^^^^

Start a new cluster specifying a name and credential to use.  A master instance
is always created and the number of exec nodes and data nodes can be specified if desired.

command line
^^^^^^^^^^^^

.. program-output:: vp-start-cluster --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Start a cluster named ``test_cluster`` with the credential ``my_ec2_account`` and start no exec nodes.

    ``vp-start-cluster --name=test_cluster --cred=my_ec2_account --num=0``


webservice url
^^^^^^^^^^^^^^

/vappio/startCluster_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

=========  ========  ======  =======================================================
Parameter  Required  Type    Meaning
=========  ========  ======  =======================================================
cluster    Yes       String  The name of the cluster to create.
num_exec   Yes       Int     The number of exec nodes to start.
num_data   Yes       Int     The number of data nodes to start.
cred_name  Yes       String  The name of the credential to use to start the cluster.
=========  ========  ======  =======================================================

webservice response
^^^^^^^^^^^^^^^^^^^
The result is a string for the task name associated with starting this cluster


vp-terminate-cluster - Terminate a cluster
------------------------------------------------

description
^^^^^^^^^^^

Terminate a running cluster and all of its exec and data nodes.


command line
^^^^^^^^^^^^
.. program-output:: vp-terminate-cluster --help


command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Terminate a cluster named ``test_cluster``:

    ``vp-terminate-cluster --name=test_cluster``

    Output

        ``None``


webservice url
^^^^^^^^^^^^^^

/vappio/terminateCluster_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

=========  ========  =======  =============================================================================================
Parameter  Required  Type     Meaning
=========  ========  =======  =============================================================================================
cluster    Yes       String   The name of the cluster.
force      No        Boolean  If the cluster is in an invalid state, such as not responding to requests, force a shut down.
=========  ========  =======  =============================================================================================

webservice response
^^^^^^^^^^^^^^^^^^^

``None``


vp-describe-cluster - Describe clusters
---------------------------------------

description
^^^^^^^^^^^

Give a list of all running clusters or provide information for a specific cluster.

command line
^^^^^^^^^^^^

.. program-output:: vp-describe-cluster --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    List all clusters

    ``vp-describe-cluster --list``

    Output::

        CLUSTER local
        CLUSTER diag-3
        CLUSTER diag-2
        CLUSTER diag-1

**Example 2**
    Show information on a specific cluster

    ``vp-describe-cluster --name=diag-1``

    Output::

        MASTER  i-84b7eb2e      diag-128-18.igs.umaryland.edu   running
        GANGLIA http://diag-128-18.igs.umaryland.edu/ganglia
        ERGATIS http://diag-128-18.igs.umaryland.edu/ergatis
        SSH     ssh -oNoneSwitch=yes -oNoneEnabled=yes -o PasswordAuthentication=no 
                -o ConnectTimeout=30 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 
                -o UserKnownHostsFile=/dev/null -q -i /mnt/keys/devel1.pem root@diag-128-18.igs.umaryland.edu


webservice url
^^^^^^^^^^^^^^

| /vappio/listClusters_ws.py
| /vappio/clusterInfo_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

Listing clusters (``/vappio/listClusters_ws.py``) takes no parameters.

Describing a specific cluster (``/vappio/clusterInfo_ws.py``) takes the following:

=========  ========  =======  =======================================================================================
Parameter  Required  Type     Meaning
=========  ========  =======  =======================================================================================
cluster    Yes       String   Name of the cluster.
partial    No        Boolean  If a cluster is unresponsive do not error out but return a partial list of information.
=========  ========  =======  =======================================================================================

webservice response
^^^^^^^^^^^^^^^^^^^

The response to listing clusters (``/vappio/listClusters_ws.py``) is a string of cluster names (strings).

The response to describing a cluster (``/vappio/clusterInfo_ws.py``) is a dictionary with the following
attributes:

=========  =============  =========================================================
Parameter  Type           Meaning
=========  =============  =========================================================
name       String         Name of the cluster.
cred       String         Name of the credential.
execNodes  Instance list  List of exec instances.
dataNodes  Instance list  List of data instances.
master     Instance       Instance description for the master.
config     Dictionary     Key value pairs of configuration options for the cluster.
=========  =============  =========================================================

Instances are defined as the following, other attributes may be present but these
are the bare minimum:

=============  ==============  =======================================================================================================
Parameter      Type            Meaning
=============  ==============  =======================================================================================================
amiId          String          The name of the image the instance is running.
instanceId     String          The unique id for the instances.
spotRequestId  String or null  If the instance is the result of a spot request this will be the spot request id string, otherwise null.
bidPrice       String or null  If the instance is a spot request this will be the price that was bid, otherwise null.
state          String          A string representing the state, valid states are pending, running and terminated.
instanceType   String          The type of the instance created.
key            String          The key the instance was created with.
instanceType   String          The instance type (m1.small for example).
publicDNS      String          The public domain name of the instance.
privateDNS     String          The private domain name of the string.
=============  ==============  =======================================================================================================

vp-add-instances - Add instances to a cluster
---------------------------------------------

description
^^^^^^^^^^^

Add exec or data instances to a running cluster.

**Note:** This tool is currently being expanded

command line
^^^^^^^^^^^^

.. program-output:: vp-add-instances --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Add 200 instances to the cluster named ``my_ec2-cluster``:
    
    ``vp-add-instances --name=my_ec2_cluster --num=200``


webservice url
^^^^^^^^^^^^^^

/vappio/addInstances_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

=========  ========  ======  ==================================== 
Parameter  Required  Type    Meaning
=========  ========  ======  ====================================
cluster    Yes       String  Name of cluster to add instances to.
num        Yes       Int     Number of exec instances to add.
=========  ========  ======  ====================================

webservice response
^^^^^^^^^^^^^^^^^^^
The response is the task name associated with adding instances
