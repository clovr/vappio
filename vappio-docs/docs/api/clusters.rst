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
Command

``vp-start-cluster --name=test_cluster --cred=my_ec2_account --num=0``

Output::

    Specify output here


webservice url
^^^^^^^^^^^^^^
/vappio/startCluster_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^
=========  ========  ======  ======================================================
Parameter  Required  Type    Meaning
=========  ========  ======  ======================================================
cluster    Yes       String  The name of the cluster to create
num_exec   Yes       Int     The number of exec nodes to start
num_data   Yes       Int     The number of data nodes to start
cred_name  Yes       String  The name of the credential to use to start the cluster
=========  ========  ======  ======================================================

webservice response
^^^^^^^^^^^^^^^^^^^
The result is a string for the task name associated with starting this cluster


vp-terminate-cluster - Terminate a cluster
------------------------------------------------

description
^^^^^^^^^^^
Terminate a running cluster and all of its exec and data nodes.

Note: This will be changing in the future to not terminate a cluster but to toggle a switch
to shut itself down before the next pay period.

command line
^^^^^^^^^^^^
.. program-output:: vp-terminate-cluster --help


command line examples
^^^^^^^^^^^^^^^^^^^^^
Command

``vp-terminate-cluster --name=test_cluster``

Output

``None``


webservice url
^^^^^^^^^^^^^^
/vappio/terminateCluster_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^
=========  ========  =======  ============================================================================================
Parameter  Required  Type     Meaning
=========  ========  =======  ============================================================================================
cluster    Yes       String   The name of the cluster
force      No        Boolean  If the cluster is in an invalid state, such as not responding to requests, force a shut down
=========  ========  =======  ============================================================================================

webesrvice response
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
List all clusters

``vp-describe-cluster --list``

Output::

    CLUSTER local
    CLUSTER diag-3
    CLUSTER diag-2
    CLUSTER diag-1

Show information on a specific cluster

``vp-describe-cluster --name=diag-1``

Output::

    MASTER  i-84b7eb2e      diag-128-18.igs.umaryland.edu   running
    GANGLIA http://diag-128-18.igs.umaryland.edu/ganglia
    ERGATIS http://diag-128-18.igs.umaryland.edu/ergatis
    SSH     ssh -oNoneSwitch=yes -oNoneEnabled=yes -o PasswordAuthentication=no -o ConnectTimeout=30 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o UserKnownHostsFile=/dev/null -q -i /mnt/keys/devel1.pem root@diag-128-18.igs.umaryland.edu


webservice url
^^^^^^^^^^^^^^
/vappio/listClusters_ws.py
/vappio/clusterInfo_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^
Listing clusters (``/vappio/listClusters_ws.py``) takes no parameters.

Describing a specific cluster (``/vappio/clusterInfo_ws.py``) takes the following:

=========  ========  =======  =====================================================================================
Parameter  Required  Type     Meaning
=========  ========  =======  =====================================================================================
cluster    Yes       String   Name of the cluster
partial    No        Boolean  If a cluster is unresponsive do not error out but return a partial list of information
=========  ========  =======  =====================================================================================

