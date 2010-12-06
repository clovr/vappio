Tasks
=====

vp-describe-task - Get information about a task
-----------------------------------------------

description
^^^^^^^^^^^

A task represents the state of a long running process.  ``vp-describe-task`` can be used
to query the state of several tasks in many ways.  The most common usage is simply to block
on a task until it is completed.  It is also useful for debugging as all of the errors generated
during the run of the process will pushed to the task.

Every task contains a state, total number of steps in that task, total number of completed steps,
a timestamp of last update, and a list of messages.  The ``JSON`` structure to this object
is described below.

command line
^^^^^^^^^^^^

.. program-output:: vp-describe-task --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Give summary information on all tasks:

    ``vp-describe-task``

    Output::

        Task: tagData-1291329692.91      Type: tagData       State: completed     Num: 1/1 (100%) LastUpdated: 2010/12/02 22:41:33 UTC


	Task: downloadTag-1291329665.33  Type: downloadTag   State: completed     Num: 2/2 (100%) LastUpdated: 2010/12/02 22:41:35 UTC


	Task: tagData-1291329694.28      Type: tagData       State: completed     Num: 1/1 (100%) LastUpdated: 2010/12/02 22:41:34 UTC


	Task: tagData-1291407449.22      Type: tagData       State: completed     Num: 1/1 (100%) LastUpdated: 2010/12/03 20:17:30 UTC


**Example 2**
    Give summary information on only those tasks that have not completed (this includes failed and running tasks):

    ``vp-describe-task --nc``

    Output::

        Task: realizeTag-1291215268.4    Type: realizeTag    State: failed        Num: 0/2 (  0%) LastUpdated: 2010/12/01 15:04:14 UTC


	Task: uploadTag-1291215267.24    Type: uploadTag     State: failed        Num: 1/2 ( 50%) LastUpdated: 2010/12/01 15:04:40 UTC


	Task: addInstances-1291216121.4  Type: addInstances  State: failed        Num: 0/1 (  0%) LastUpdated: 2010/12/01 15:08:42 UTC


	Task: startCluster-1291319864.71 Type: startCluster  State: failed        Num: 0/2 (  0%) LastUpdated: 2010/12/02 19:57:48 UTC


**Example 3**
    Block on all running task printing updates periodically.  The output to this is not shown because it involves a periodic update
    of the screen.

    ``vp-describe-task --block``

**Example 4**
    Block on a specific task.

    ``vp-describe-task --block startCluster-1291319864.71``

**Example 5**
    Show all message associated with a particular task.

    **Note:** You can list as many tasks as you want, none of these options are limited to a single task

    ``vp-describe-task --show-all startCluster-1291319864.71``

    Output::

        Task: startCluster-1291319864.71 Type: startCluster  State: failed        Num: 0/2 (  0%) LastUpdated: 2010/12/02 19:57:48 UTC
        Notification - 2010/12/02 19:57:44 UTC: Starting test
        Debug - 2010/12/02 19:57:44 UTC: Starting master
        Notification - 2010/12/02 19:57:44 UTC: Loading credential...
        Error - 2010/12/02 19:57:48 UTC: Unable to run program u'/opt/ec2-api-tools-1.3-42584/bin/ec2-run-instances -K /tmp/diag_key.pem -C /tmp/diag_cert.pem  -k vappio_00 -t m1.small -g vappio -g web -n 1  -f /tmp/master_user_data.sh' with exit code 1
        Stacktrace:
                Traceback (most recent call last):
                  File "/opt/vappio-py/vappio/tasks/utils.py", line 85, in runTask
                    f()
                  File "/opt/vappio-py/vappio/tasks/utils.py", line 98, in <lambda>
                    return runTask(options(optionsTaskName), lambda : func(options, args))
                  File "/opt/vappio-py/vappio/cli/remote/startClusterR.py", line 99, in main
                    cl = cl.startMaster(updateCluster)
                  File "/opt/vappio-py/vappio/cluster/control.py", line 112, in startMaster
                    dataFile)[0]
                  File "/opt/vappio-py/vappio/cluster/control.py", line 396, in runInstancesWithRetry
                    userDataFile=dataFile)
                  File "/opt/vappio-py/vappio/ec2/control.py", line 248, in runInstances
                    runWithCred(cred, cmd, _instanceParse, log=log)
                  File "/opt/vappio-py/vappio/ec2/control.py", line 114, in runWithCred
                    return commands.runSingleProgramEx(cmdPrefix + ' '.join(addCredInfo(cmd, cred)), stdoutf, stderrf, log=log, addEnv=cred.env)
                  File "/opt/vappio-py/igs/utils/commands.py", line 121, in runSingleProgramEx
                    raise ProgramRunError(pr.cmd, pr.exitCode)
                ProgramRunError: Unable to run program u'/opt/ec2-api-tools-1.3-42584/bin/ec2-run-instances -K /tmp/diag_key.pem -C 
                                 /tmp/diag_cert.pem  -k vappio_00 -t m1.small -g vappio -g web -n 1  -f /tmp/master_user_data.sh' with exit code 1

    The output shows that this tag failed, how many steps through starting a cluster it made it (none) and the last update time.  
    It is also shown that There were 2 notification messages, 1 debug, and 1 error message.  This task failed trying to run 
    the described program and the stack trace is shown.

**Note:** There are several options for ``vp-describe-task``.  Almost all of them work well together and one is encouraged to experiment
with them.

webservice url
^^^^^^^^^^^^^^

/vappio/task_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

**Note:** The webservice interface is under considerable overhaul

=========  ========  ======  ==========================
Parameter  Required  Type    Meaning
=========  ========  ======  ==========================
cluster    Yes       String  Name of cluster to run on.
=========  ========  ======  ==========================


webservice response
^^^^^^^^^^^^^^^^^^^

The response is always a list of tasks.  Each task looks like the following:

==============  ========  ===============  =======================================================================================
Parameter       Required  Type             Meaning
==============  ========  ===============  =======================================================================================
state           Yes       String           The state of the task (idle, running, failed, completed).
name            Yes       String           The name of the task.
timestamp       Yes       Float            Decimal value for the timestamp.
tType           Yes       String           The type of operation the task is associated with (this is not a closed set of values).
completedTasks  Yes       Int              Number of steps completed.
numTasks        Yes       Int              Number of steps in the task.
messages        Yes       Dictionary List  A list of ``message`` objects, described below.
==============  ========  ===============  =======================================================================================


Each ``message`` object is a dictionary that requires a ``mtype`` key.  The ``mtype`` key describes the
type of message the entry is and has one of the following values: ``notification``, ``silent``, ``error``, and ``result``.

The following describes what the ``message`` will look like depending on the value of ``mtype``:

``notification`` or ``silent``:

=========  ======  =================================
Parameter  Type    Meaning
=========  ======  =================================
timestamp  Float   Time the message was added.
text       String  Text of the notification message.
=========  ======  =================================

``result``:

=========  ======  ===========================
Parameter  Type    Meaning
=========  ======  ===========================
timestamp  Float   Time the message was added.
result     String  Text of the result.
=========  ======  ===========================

``error``:

==========  ======  ==================================
Parameter   Type    Meaning
==========  ======  ==================================
timestamp   Float   Time the message was added.
stacktrace  String  The stacktrace, could be empty.
text        String  Description of the error.
name        String  Name of the error, could be empty.
==========  ======  ==================================

