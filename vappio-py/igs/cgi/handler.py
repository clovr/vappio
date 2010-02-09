##
# This is a little framework to make it easier and less error prone to write CGI scripts.
# This defines an object which should be implemented by anyone writing an CGI script.  The object
# is then used to construct the response.
import json
import cgitb


class CGIPage:
    """
    A class which one implements to create a page that is called via CGI.

    This base class provides some reasonable defaults.  The members are:
    contentType, default = Content-Type: text/html
    headers,     default = {}
    body(self)   - This is a member function which is called and should return a string
    """

    def __init__(self, contentType='Content-Type: text/html', headers=None):
        self.contentType = contentType
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers


    def body(self):
        raise Exception('Please implement me')



def generatePage(cgiPage):
    """
    Takes an instance of CGIPage and generates a page from it,
    sending the proper headers and all that
    """
    cgitb.enable()
    print cgiPage.contentType
    if cgiPage.headers:
        print '\n'.join([h + ': ' + v for h, v in cgiPage.headers.iteritems()])
    print
    try:
        print cgiPage.body()
    except Exception, err:
        print json.dumps([False, str(err)])
    
