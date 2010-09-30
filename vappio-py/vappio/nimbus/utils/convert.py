##
# This has tools to convert a nimbus cert into a cert that can be used with the EC2 tools
import os

from igs.utils.commands import ProgramRunError, runSystemEx, runSystem


def convertCert(instream, outstream):
    writeData = False
    for line in instream:
        if 'BEGIN CERTIFICATE' in line:
            writeData = True

        if writeData:
            outstream.write(line)


def convertKey(inname, outname):
    """
    This just calls an openssl command.

    The user will have to type in their password
    """

    ##
    # Using os.system here because we want to let the user type in
    cmd = """openssl rsa -in %s -out %s""" % (inname, outname)
    code = os.system(cmd)

    if code != 0:
        raise ProgramRunError(cmd, code)

    runSystemEx('chmod 400 ' + outname)


def addJavaCert(outputdir, host, port):
    """This installs a java cert.  It is assumed that install-cert.sh is in the PATH"""

    runSystemEx("""echo 1 | install-cert.sh %s:%d""" % (host, port))
    runSystem("""mv jssecacerts %s""" % (outputdir,))




def test():
    convertCert(open('/home/mmatalka/.globus/usercert.pem'), open('/home/mmatalka/.globus/usercert-ec2.pem', 'w'))
    convertKey('/home/mmatalka/.globus/userkey.pem', '/home/mmatalka/.globus/userkey-ec2.pem')
    addJavaCert('/home/mmatalka/.globus', 'tp-vm1.ci.uchicago.edu', 8445)
    


    

        

    
