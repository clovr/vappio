Tasklets
========

What is a tasklet?
------------------

A ``tasklet`` represents a small peice of work that runs in combination with other ``tasklets`` to perform a task.
An example of a ``tasklet`` might be calculating how many CPU hours a pipeline will take then resizing
the cluster to handle the workload.  Individual ``tasklets`` should generally be seen similar to UNIX utilities
such as ``ls`` or ``grep`` which perform a single function well and are designed to be composed with other tools through
``stdin`` and ``stdout``.


vp-run-metrics - Run a tasklet
------------------------------

description
^^^^^^^^^^^

Runs a tasklet on a cluster.

command line
^^^^^^^^^^^^

.. program-output:: vp-run-metrics --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Run a ``tasklet`` to calculate the number of CPU hours a BLAST run will take on the pipeline named ``clovr_search_12-01-2010-15:07:00``.
    This demonstrates that a pipeline name can be specified, this is optional.  The ``-c`` option can also be used to add config options
    to the run.  ``--pipeline-name`` specifies that the configuration from a particular pipeline should be passed as the initial input
    to the ``tasklet`` run and any output variables should be added or updated in the pipeline configuration.

    ``vp-run-metrics --pipeline-name=clovr_search_12-01-2010-15:07:00 -c cluster.CLUSTER_NAME=local "translate-keys input.REF_DB_TAG=misc.REP_DB | filter-keys input.INPUT_TAG cluster.CLUSTER_NAME misc.PROGRAM misc.REP_DB | tag-is-fasta | sequence-stats | cunningham_calc_cpu_hours"``


   Output::

        Task: runMetric-1291216072.42 Type: runMetric     State: completed     Num: 7/7 (100%) LastUpdated: 2010/12/01 15:08:10 UTC
	Debug - 2010/12/01 15:07:55 UTC: Starting to run /opt/vappio-metrics/get-pipeline-conf clovr_search_12-01-2010-15:07:00 | 
        /opt/vappio-metrics/translate-keys input.REF_DB_TAG=misc.REP_DB | /opt/vappio-metrics/filter-keys input.INPUT_TAG 
        cluster.CLUSTER_NAME misc.PROGRAM misc.REP_DB | /opt/vappio-metrics/tag-is-fasta | /opt/vappio-metrics/sequence-stats | 
        /opt/vappio-metrics/cunningham_calc_cpu_hours | /opt/vappio-metrics/set-pipeline-conf clovr_search_12-01-2010-15:07:00
	Notification - 2010/12/01 15:08:10 UTC: Completed
	Result - 2010/12/01 15:08:10 UTC: {u'mtype': u'result', u'timestamp': 1291216090.175765, u'result': u'kv
	\ncluster.CLUSTER_NAME=local\ninput.INPUT_TAG=NC_000964_peps\nmisc.PROGRAM=blastp
	\nmisc.REP_DB=NC_000964_blastpdb\nparams.MAX_QUERY_SEQ_LEN=5488\nparams.MIN_QUERY_SEQ_LEN=20
    	\nparams.AVG_QUERY_SEQ_LEN=297.614859927\nparams.NUM_QUERY_SEQ=4105
        \npipeline.COMPUTED_CPU_HOURS=1.00539440771\n'}

webservice url
^^^^^^^^^^^^^^

/vappio/runMetrics_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

=========  ========  ==========  ============================================================================
Parameter  Required  Type        Meaning
=========  ========  ==========  ============================================================================
cluster    Yes       String      Name of cluster to run ``tasklet`` on.
conf       Yes       Dictionary  Dictionary of key-value pairs to pass as initial input to first ``tasklet``.
metrics    Yes       String      A string of ``tasklets`` to run seperated by ``|``.
=========  ========  ==========  ============================================================================

webservice response
^^^^^^^^^^^^^^^^^^^

The name of the task associated with the ``tasklet`` run.
