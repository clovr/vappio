Pipelines and Protocols
=======================

vp-describe-protocols - List protocols and config options
---------------------

description
^^^^^^^^^^^
The system can have many protocols associated with it.  A protocol is the description
of actions to perform on a dataset and a pipeline is a running instance of a protocol.
``vp-describe-protocols`` can list the protocols available by the system and their
config options.

command line
^^^^^^^^^^^^
.. program-output:: vp-describe-protocols --help

command line examples
^^^^^^^^^^^^^^^^^^^^^
**Example 1**
    List all protocols available

    ``vp-describe-protocols``

    Output::

        PROTOCOL        clovr_comparative
        PROTOCOL        clovr_assembly_celera
        PROTOCOL        clovr_pangenome
        PROTOCOL        clovr_16S
        PROTOCOL        clovr_microbe_illumina
        PROTOCOL        clovr_metagenomics_orfs
        PROTOCOL        clovr_search
        PROTOCOL        clovr_microbe_annotation
        PROTOCOL        clovr_metatranscriptomics
        PROTOCOL        clovr_sleep
        PROTOCOL        clovr_search_webfrontend
        PROTOCOL        clovr_mugsy
        PROTOCOL        clovr_metagenomics_noorfs
        PROTOCOL        clovr_total_metagenomics
        PROTOCOL        clovr_microbe454

**Example 2**
    Create a config file with the options from the ``clovr_search`` protocol.  This config file can then be modified
    in order to run a pipeline.

    ``vp-describe-protocols -p clovr_search > clovr_search.conf``

    Output::

``None``

**Example 3**
    Create a config file with the options from the ``clovr_search`` protocol but specify some of the config options
    on the config file.

    ``vp-describe-protocols -p clovr_search -c input.INPUT_TAG=my_input_tag -c misc.PROGRAM=blastp -c input.REF_DB_TAG> clovr_search.conf``

    Output::

``None``

webservice url
^^^^^^^^^^^^^^
/vappio/listProtocols_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^
=============  ========  ======  ===========================================
Parameters     Required  Type    Meaning
=============  ========  ======  ===========================================
cluster        Yes       String  Name of the cluster to query protocols
protocol_name  No        String  Specific protocol get configuration options
=============  ========  ======  ===========================================

webservice response
^^^^^^^^^^^^^^^^^^^
If ``protocol_name`` is not specified then a list of protocol names is returned.  If ``protocol_name`` is 
specified than a list of lists where the first element in the inner list is the config name and the second
element in the inner list is a dictionary where each dictionary has the possible values:

==========  ========  =====================  ==================================================================
Parameter   Required  Type                   Meaning
==========  ========  =====================  ==================================================================
default     Yes       String or Int or List  The default value for the config option.  Can be one of many types
display     No        String                 The name the config option should be displayed as in a UI
desc        Yes       String or null         The description of the config option
source      No        String                 The source the option should be populated then
visibility  No        String                 default_hidden or always_hidden
choices     No        String list            A list of values the input of the option should be restricted to
==========  ========  =====================  ==================================================================

vp-run-pipeline - Run a pipeline
--------------------------------

description
^^^^^^^^^^^
After a protocol has been configured the config file can be used to run a pipeline.  All pipelines must have a unique
name.  A pipeline is run with the same name as a previous pipeline, the task id for the previous pipeline is returned.
Pipelines can also be resumed if they had failed previously.

command line
^^^^^^^^^^^^
.. program-output:: vp-run-pipeline --help

command line examples
^^^^^^^^^^^^^^^^^^^^^
**Example 1**
    Run a ``clovr_search`` pipeline with the config file ``clovr_search.config`` named ``clovr_search_test_run``:

    ``vp-run-pipeline --pipeline=clovr_search --pipeline-name=clovr_search_test_run --pipeline_config=clovr_search.config``

**Example 2**
    If a pipeline failed but it can be fixed and resumed, the --resume option allows the continuation of a pipeline.

    ``vp-run-pipeline --resume --pipeline-name=clovr_search_test_run``

webservice url
^^^^^^^^^^^^^^
/vappio/runPipeline_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^
===============  ========  ==========  ==============================================================
Parameter        Required  Type        Meaning
===============  ========  ==========  ==============================================================
cluster          Yes       String      Name of cluster to run the pipeline on
pipeline         Yes       String      The type of pipeline to run, for example clovr_search
pipeline_name    Yes       String      The name of the pipeline
pipeline_config  Yes       Dictionary  Key value pairs representing the configuration of the pipeline
pipeline_queue   Yes       String      The queue to run the pipeline in
overwrite        Yes       Boolean     Overwrite the pipeline if it already exists
resume           Yes       Boolean     Resume the pipeline if it has failed
===============  ========  ==========  ==============================================================

vp-describe-pipeline - Describe the pipelines
---------------------------------------------

description
^^^^^^^^^^^
Get a list of pipelines running on a cluster

command line
^^^^^^^^^^^^
.. program-output:: vp-describe-pipeline --help

command line examples
^^^^^^^^^^^^^^^^^^^^^
Command

    ``vp-describe-pipeline``

Output::

                                    Name                       TaskName     Status                 Type   Complete      Total
        clovr_search_11-29-2010-15:01:57      runPipeline-1291042950.69   complete         clovr_search          6          6
        clovr_search_12-01-2010-15:07:00      runPipeline-1291216061.62   complete         clovr_search          6          6
                      clovr_search_24672      runPipeline-1291215248.45      error        clovr_wrapper          2          6
                      clovr_search_28775      runPipeline-1291216021.45   complete        clovr_wrapper          6          6
                       clovr_search_4339       runPipeline-1291042918.5   complete        clovr_wrapper          6          6
                       clovr_search_8090      runPipeline-1291046316.89      error        clovr_wrapper          4          6

webservice url
^^^^^^^^^^^^^^
/vappio/pipelineStatus_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^
=========  ========  ======  ===============
Parameter  Required  Type    Meaning
=========  ========  ======  ===============
cluster    Yes       String  Name of cluster
=========  ========  ======  ===============

webservice response
^^^^^^^^^^^^^^^^^^^
A list of dictionaries is returned with the following attributes

===============  ======  =================================================
Parameter        Type    Meaning
===============  ======  =================================================
name             String  Name of th epipeline
task_name        String  Name of task associated with the running pipeline
status           String  Current status of the pipeline
type             String  Type of pipeline i.e. clovr_search
completed_tasks  Int     Number of completed tasks
total_tasks      Int     Total number of steps
===============  ======  =================================================

