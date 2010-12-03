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

There are a number of ways to use ``vp-add-dataset``, it provides a lot of functionality.  Almost all of the combinations
of options work together.  Play around with the options to get comfortable with it.

**Example 8**
    Overwrite the tag ``example6`` with the file ``/foo/bar/baz`` and the contents the directory ``/path/to/boom``:

    ``vp-add-dataset --tag-name=example6 -o -r /foo/bar/baz /path/to/boom``

**Example 9**
    Make a tag called ``example9`` that has all the files that start with foo in ``/path/to/boom`` in it and add two
    metadata keys to it, ``filetype`` and ``author``:

    ``vp-add-dataset --tag-name=example9 -m filetype=foos -m author=me_of_course /path/to/boom/foo*``


webservice url
^^^^^^^^^^^^^^
/vappio/tagData_ws.py

webservice parameters
^^^^^^^^^^^^^^^^^^^^^
============  ========  ==============  =================================================================================================================
Parameter     Required  Type            Meaning
============  ========  ==============  =================================================================================================================
cluster       Yes       String          The name of the cluster to tag data on
tag_name      Yes       String          The name of the tag
tag_base_dir  Yes       String or null  If present, the base directory of the tag
files         Yes       String list     A list of filenames to tag, an empty list is acceptable
recursive     Yes       Boolean         Recursively tag the elements in ``files``
expand        Yes       Boolean         Example any compressed files found in the tagging process
compress      Yes       String or null  If the contents of the tag should be compressed give the base directory to compress into
append        Yes       Boolean         Append to the curent tag
overwrite     Yes       Boolean         Overwrite the tag or not.  If the tag is already present and append is not specified the operation becomes a noop
tag_metadata  Yes       Dictionary      Key value pairs of metadata for the tag
============  ========  ==============  =================================================================================================================
