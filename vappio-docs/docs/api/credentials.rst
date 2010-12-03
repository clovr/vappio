Credentials
===========

vp-add-credential - Adding a credential
---------------------------------------

description
^^^^^^^^^^^
Add or overwrite a new credential to the database


command line
^^^^^^^^^^^^
.. program-output:: vp-add-credential --help


command line examples
^^^^^^^^^^^^^^^^^^^^^
Command

``vp-add-credential --cred-name=foo --ctype=ec2 -c /path/to/cert.pem -p /path/to/pkey.pem``

Output

``None``


webservice url
^^^^^^^^^^^^^^
/vappio/credential_ws.py


webservice parameters
^^^^^^^^^^^^^^^^^^^^^
===============  ========  ==========  ===================================================
Paramater        Required  Type        Meaning
===============  ========  ==========  ===================================================
credential_name  Yes       String      The credential name
description      Yes       String      A description of the credential
ctype            Yes       String      The credential type (diag, nimbus, ec2, local, etc)
cert             Yes       String      The contents of the certificate file
pkey             Yes       String      The contents of the private key file
metadata         Yes       Dictionary  Key value pairs for metadata used in the credential
===============  ========  ==========  ===================================================


webservice response
^^^^^^^^^^^^^^^^^^^
``None``


vp-describe-credentials - Describing credentials
------------------------------------------------

description
^^^^^^^^^^^
Get a list of the available credentials as well as the number of running instances
associated with that credential.


command line
^^^^^^^^^^^^
.. program-output:: vp-describe-credentials --help


command line example
^^^^^^^^^^^^^^^^^^^^
Command

``vp-describe-credentials``

Output::

    CRED    local   0
    CRED    diag    0


webservice url
^^^^^^^^^^^^^^
/vappio/credential_ws.py


webservice parameters
^^^^^^^^^^^^^^^^^^^^^
================  ========  ===============  ===================================================================
Parameter         Required  Type             Meaning
================  ========  ===============  ===================================================================
credential_names  No        List of Strings  This list limits the returned credentials to just those in the list
================  ========  ===============  ===================================================================


webservice response
^^^^^^^^^^^^^^^^^^^
A list of dictionaries is returned where each dictionary contains the following keys:

=============  ======  =========================================================
Parameter      Type    Meaning
=============  ======  =========================================================
name           String  The name of the credential
description    String  The description of the credential
num_instances  Int     The number of active instances running on that credential
=============  ======  =========================================================
