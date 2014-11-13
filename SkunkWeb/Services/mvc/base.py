"""

Contains a BaseController class suitable as a base class for
controllers, with some convenience methods.

"""

import SkunkWeb
from computils import stringcomp
import os
import re
import string
import time
import Cookie

_schemepat=re.compile('^[a-z]+://.*')

try:
    # python 2.5
    from httplib import responses as http_responses
except ImportError:
    import web.protocol as P
    http_responses=dict((x,y[4:]) for x, y in P._http_statuses.iteritems() if not y.endswith('unused'))
    del P


ERROR_TEMPLATES={
    'text/plain' : string.Template("$message"),
    'text/html' :  string.Template("<html><head><title>$message</title></head><body><h1>$message</h1></body></html>")}


class BaseController(object):

    def connection():
        def fget(self):
            return SkunkWeb.Context.connection
        return fget
    connection=property(connection())

    def http_error(self, status, message=None, mimetype=None, template=None):
        if status not in http_responses:
            raise ValueError, "invalid status: %s" % status
        if mimetype is None:
            mimetype=SkunkWeb.Configuration.defaultErrorMimetype
        elif mimetype not in ERROR_TEMPLATES:
            raise ValueError, "unsupported mimetype for error response: %s" % mimetype
        if message is None:
            message=http_responses[status]
        conn=self.connection
        conn.setStatus(status)
        if template is None:
            template=ERROR_TEMPLATES[mimetype]
        else:
            if not hasattr(template, "safe_substitute"):
                template=string.Template(template)
        conn.setContentType(mimetype)
        return template.safe_substitute(message=message)
    

    def do404(self, message=None):
        # special case 404s to use the preexisting SkunkWeb 404 mechanism
        conn=self.connection
        conn.setStatus(404)
        conn.setContentType('text/html')
        return stringcomp(SkunkWeb.Configuration.notFoundTemplate,
                         message=message)

    def do401(self, message=None, mimetype=None, template=None):
        return self.http_error(status, message, mimetype, template)


    def redirect(self, url, status=301):
        if not _schemepat.match(url):
            url=os.path.normpath(os.path.join(self.connection.uri, url))
        self.connection.redirect(url, status)
        return "redirecting to %s" % url

    def flash(self, message):
        """
        flash a message into a cookie
        """
        cookie=self.connection.responseCookie
        cookie['flash']=message
        cookie['flash']['path']='/'
        cookie['flash']['expires']=time.time()+1000

    def get_flash(self, default=None, responseCookie=None):
        """
        get a flashed message
        """
        try:
            message=self.connection.requestCookie['flash'].value
        except KeyError:
            return default
        else:
            if responseCookie is None:
                responseCookie=self.connection.responseCookie
            responseCookie['flash']=''
            responseCookie['flash']['expires']=-99999
            return message


class Response(Exception,object):
    def __init__(self):
        self.status=200
        self.buffer=[]
        self.headers=[]
        self.cookie=Cookie.SimpleCookie()


    def http_error(self, status, message=None, mimetype=None, template=None):
        if status not in http_responses:
            raise ValueError, "invalid status: %s" % status
        if mimetype is None:
            mimetype=SkunkWeb.Configuration.defaultErrorMimetype
        elif mimetype not in ERROR_TEMPLATES:
            raise ValueError, "unsupported mimetype for error response: %s" % mimetype
        if message is None:
            message=http_responses[status]
        self.status=status
        if template is None:
            template=ERROR_TEMPLATES[mimetype]
        else:
            if not hasattr(template, "safe_substitute"):
                template=string.Template(template)
        self.headers.append(('Content-Type', mimetype))
        self.write(template.safe_substitute(message=message))

    def write(self, data):
        self.buffer.append(data)

    def __call__(self, conn):
        conn.setStatus(self.status)
        if self.headers:
            for h in self.headers:
                conn.responseHeaders[h[0]]=h[1]
        if self.cookie:
            conn.responseCookie.update(self.cookie)
        for b in self.buffer:
            conn.write(b)


    def redirect(self, url, status=301, message=None):
        if not _schemepat.match(url):
            url=os.path.normpath(os.path.join(SkunkWeb.Context.connection.uri,
                                              url))
        self.status=status
        self.headers.append(('Location', url))
        if message is None:
            message="redirecting to $url"
        self.write(string.Template(message).safe_substitute(url=url))

    def flash(self, message):
        """
        flash a message into a cookie
        """
        self.cookie['flash']=message
        self.cookie['flash']['path']='/'
        self.cookie['flash']['expires']=time.time()+1000

        
def HTTPError(status, message=None, mimetype=None, template=None):
    r=Response()
    r.http_error(status, message, mimetype, template)
    return r
        
    
__all__=['BaseController', 'Response', 'HTTPError']
