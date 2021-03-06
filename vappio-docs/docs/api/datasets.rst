Datasets
========

vp-add-dataset - Register a dataset
-----------------------------------

description
^^^^^^^^^^^

In order to be used with other tools a dataset must first be registered.  A set of files is
given a name to be grouped by and metadata describing it.  In order to transfer data it
must first be tagged.

command line
^^^^^^^^^^^^

.. program-output:: vp-add-dataset --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Add a file called ``/foo/bar/baz`` under the tag name ``example1``:

    ``vp-add-dataset --tag-name=example1 /foo/bar/baz``

    Output::

        Task: tagData-1291407449.22 Type: tagData       State: completed     Num: 1/1 (100%) LastUpdated: 2010/12/03 20:17:30 UTC
        Notification - 2010/12/03 20:17:29 UTC: Tagging example1
        Notification - 2010/12/03 20:17:30 UTC: Tagging complete


**The output for the following examples will all be similar to the above output so it is not included**

**Example 2**
    Add a file called ``/foo/bar/baz`` under the tag name ``example2`` but specify a tag-base-dir.  This states what portion of the
    directory to consider the root directory.  When the tag is uploaded this portion of the file name will be stripped off.

    ``vp-add-dataset --tag-name=example2 --tag-base-dir=/foo/bar /foo/bar/baz``


**Example 3**
    Add a dataset called ``example3`` that is every file in the directory ``/path/to/boom``:

    ``vp-add-dataset --tag-name=example3 -r /path/to/boom``


**Example 4**
    Add a dataset called ``example4`` that is every file in the directory ``/path/to/boom`` and all compressed files in it are expanded:

    ``vp-add-dataset --tag-name=example4 -r -e /path/to/boom``

    **Note:** the ``-e`` works if you are just tagging a file like in the first example.

**Example 5**
    Append the files in ``/path/to/boom`` to the tag ``example5``:

    ``vp-add-dataset --tag-name=example5 -a -r /path/to/boom``

**Example 6**
    Tag the files in ``/path/to/boom`` and create a compressed copy of the contents of the tag to ``/path/to/compressed``:

    ``vp-add-dataset --tag-name=example6 -r --compress=/path/to/compressed /path/to/boom``

    **Note:** This last example will create a file called ``/path/to/compressed/boom.tar.gz`` which are the contents
    of the tag.

**Example 7**
    Take the tag ``example6`` from above and append the the file ``/foo/bar/baz`` to it and compress the contents of the tag again:

    ``vp-add-dataset --tag-name=example6 -a --compress=/path/to/compressed /foo/bar/baz``

**Example 8**
    Overwrite the tag ``example6`` with the file ``/foo/bar/baz`` and the contents the directory ``/path/to/boom``:

    ``vp-add-dataset --tag-name=example6 -o -r /foo/bar/baz /path/to/boom``

**Example 9**
    Make a tag called ``example9`` that has all the files that start with ``foo`` in ``/path/to/boom`` in it and add two
    metadata keys to it, ``filetype`` and ``author``:

    ``vp-add-dataset --tag-name=example9 -m filetype=foos -m author=me_of_course /path/to/boom/foo*``


There are a number of ways to use ``vp-add-dataset``, it provides a lot of functionality.  Almost all of the combinations
of options work together.  Play around with the options to get comfortable with it.

webservice url
^^^^^^^^^^^^^^

/vappio/tagData_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

============  ========  ==============  ==================================================================================================================
Parameter     Required  Type            Meaning
============  ========  ==============  ==================================================================================================================
cluster       Yes       String          The name of the cluster to tag data on.
tag_name      Yes       String          The name of the tag.
tag_base_dir  Yes       String or null  If present, the base directory of the tag.
files         Yes       String list     A list of filenames to tag, an empty list is acceptable.
recursive     Yes       Boolean         Recursively tag the elements in ``files``.
expand        Yes       Boolean         Example any compressed files found in the tagging process.
compress      Yes       String or null  If the contents of the tag should be compressed give the base directory to compress into.
append        Yes       Boolean         Append to the curent tag.
overwrite     Yes       Boolean         Overwrite the tag or not.  If the tag is already present and append is not specified the operation becomes a noop.
tag_metadata  Yes       Dictionary      Key value pairs of metadata for the tag.
============  ========  ==============  ==================================================================================================================

webservice response
^^^^^^^^^^^^^^^^^^^

The return is the name of the task associated with tagging the data.

vp-transfer-dataset - Upload a dataset
--------------------------------------

description
^^^^^^^^^^^

This uploads a dataset.  This is being expanded to support upload and download from any cluster to another cluster.

command line
^^^^^^^^^^^^

.. program-output:: vp-transfer-dataset --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Uploaded a tag named ``example_tag`` to cluster ``my_ec2_cluster``:

    ``vp-transfer-dataset --tag-name=example_tag --dst-cluster=my_ec2_cluster``


webservice url
^^^^^^^^^^^^^^

/vappio/uploadTag_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

===========  ========  =======  ==========================================================
Parameter    Required  Type     Meaning
===========  ========  =======  ==========================================================
tag_name     Yes       String   The name of the tag to transfer.
src_cluster  Yes       String   The name of the source cluster, *should be local for now*.
dst_cluster  Yes       String   Name of the destination cluster.
expand       Yes       Boolean  Should the files be expanded after upload.
compress     Yes       Boolean  Should the files be compressed after upload.
===========  ========  =======  ==========================================================

webservice response
^^^^^^^^^^^^^^^^^^^

The name of the task associated with the upload


vp-download-dataset - Download a dataset
--------------------------------------

description
^^^^^^^^^^^

This downloads a dataset.  This will be removed in the future, ``vp-transfer-dataset`` will be used for both upload and download

command line
^^^^^^^^^^^^

.. program-output:: vp-download-dataset --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    Downloads a tag named ``example_tag`` from cluster ``my_ec2_cluster``:

    ``vp-download-dataset --tag-name=example_tag --src-cluster=my_ec2_cluster``


webservice url
^^^^^^^^^^^^^^

/vappio/downloadTag_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

===========  ========  =======  ===========================================================
Parameter    Required  Type     Meaning
===========  ========  =======  ===========================================================
tag_name     Yes       String   The name of the tag to transfer.
src_cluster  Yes       String   The name of the source cluster.
dst_cluster  Yes       String   Name of the destination cluster, *should be local for now*.
expand       Yes       Boolean  Should the files be expanded after download.
compress     Yes       Boolean  Should the files be compressed after download.
===========  ========  =======  ===========================================================

webservice response
^^^^^^^^^^^^^^^^^^^

The name of the task associated with the upload

vp-describe-dataset - Get information about datasets
----------------------------------------------------

description
^^^^^^^^^^^

With a dataset registered with the system the files and metadata can be queried.

**Note:** Datasets are being expanded upon and redefined, this data will change.

command line
^^^^^^^^^^^^

.. program-output:: vp-describe-dataset --help

command line examples
^^^^^^^^^^^^^^^^^^^^^

**Example 1**
    List all registered datasets:

    ``vp-describe-dataset``

    Output::

        TAG     clovr-core-set-aligned-imputed-fasta
	TAG     diag-2-iozone-test
	TAG     clovr_search_11-29-2010-15:01:57_blastall_raw
	TAG     clovr-prok-db
	TAG     test-iozone-test
	TAG     ncbi-nr
	TAG     clovr-cogdb

**Example 2**
    List files and metadata about a particular dataset:

    ``vp-describe-dataset --tag-name=clovr_search_12-01-2010-15:07:00_blastall_raw``

    Output::

        FILE    /mnt/output/clovr_search_12-01-2010-15:07:00/ncbi-blastall/6_default/i1/g3/NC_000964_1.ncbi-blastall.raw
	FILE    /mnt/output/clovr_search_12-01-2010-15:07:00/ncbi-blastall/6_default/i1/g4/NC_000964_4.ncbi-blastall.raw
	FILE    /mnt/output/clovr_search_12-01-2010-15:07:00/ncbi-blastall/6_default/i1/g1/NC_000964_2.ncbi-blastall.raw
	FILE    /mnt/output/clovr_search_12-01-2010-15:07:00/ncbi-blastall/6_default/i1/g2/NC_000964_3.ncbi-blastall.raw
	METADATA        pipeline_configs.clovr_search_12-01-2010-15:07:00.env.METHOD    dhcp
	METADATA        pipeline_configs.clovr_search_12-01-2010-15:07:00.VAPPIO_CLI    /opt/vappio-py/vappio/cli/
	METADATA        tag_base_dir    /mnt/output/clovr_search_12-01-2010-15:07:00
	METADATA        pipeline_configs.clovr_search_12-01-2010-15:07:00.NODE_TYPE     MASTER
	METADATA        pipeline_configs.clovr_search_12-01-2010-15:07:00.dirs.clovr_project    /mnt/projects/clovr
	METADATA        pipeline_configs.clovr_search_12-01-2010-15:07:00.cluster.CLUSTER_NAME  local
	METADATA        pipeline_configs.clovr_search_12-01-2010-15:07:00.cluster.EXEC_NODES    0

webservice url
^^^^^^^^^^^^^^

/vappio/queryTag_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^

=========  ========  ===========  ========================================================
Parameter  Required  Type         Meaning
=========  ========  ===========  ========================================================
cluster    Yes       String       Name of cluster to query.
tag_name   Yes       String List  List of tags to get info for, an empty list of all tags.
=========  ========  ===========  ========================================================

webservice response
^^^^^^^^^^^^^^^^^^^

A list of datasets is returned where each entry is a dictionary containing the following values:

============  ===========  =================================================================
Parameter     Name         Meaning
============  ===========  =================================================================
name          String       Name of the dataset.
files         String List  A list of all the files in the dataset.
metadata.???  String       All metadata is stored with the string 'metadata.' infront of it.
============  ===========  =================================================================
