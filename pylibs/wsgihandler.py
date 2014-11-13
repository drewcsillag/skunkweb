"""
A skunkweb handler for WSGI applications.

This module is a stop-gap. The implementation is somewhat backwards,
in that the WSGI environment is constructed from the CONNECTION
object, and the CONNECTION object is used to write the response; in
future, CONNECTION will become a wrapper around wsgi rather than the
other way round.  Also, note that the handler is a wrapper around a
specific WSGI application and has no dispatching capabilities;
dispatching therefore needs to be handled at the WSGI level, or the
handler needs to be further wrapped or subclassed to provide
dispatching.

Some of the WSGI code is directly taken from the WSGI PEP (#0333).

"""

import logging
from cStringIO import StringIO

class LogStream(object):
    def __init__(self, logfunc):
        self.logfunc=logfunc

    def write(self, message):
        for line in message.rstrip().split('\n'):
            self.logfunc(line)

    def flush(self):
        pass

    def writelines(self, seq):
        for line in seq:
            self.write(line)
    

class WSGIHandler(object):

    def __init__(self, application):
        self.application=application

    def get_wsgi_environ(self, connection):
        environ=connection.env.copy()
        environ['wsgi.input']=StringIO(connection._stdin)
        environ['wsgi.errors']=LogStream(logging.getLogger('wsgierror').error)
        environ['wsgi.version']=(1,0)
        environ['wsgi.multithread']=False
        environ['wsgi.multiprocess']=True
        environ['wsgi.run_once']=False
        if environ.get('HTTPS','off') in ('on','1'):
            environ['wsgi.url_scheme'] = 'https'
        else:
            environ['wsgi.url_scheme'] = 'http'
        return environ

    def __call__(self, connection, sessionDict=None):
        return self.call_application(connection)
    
    def call_application(self, connection):
        environ=self.get_wsgi_environ(connection)
        headers_set=[]
        headers_sent=[]
        output=connection._output
        def write(data):
            if not headers_set:
                raise AssertionError("write() before start_response()")
            elif not headers_sent:
                 status, response_headers = headers_sent[:] = headers_set
                 connection.responseHeaders['Status']=status
                 for hk, hv in response_headers:
                     # N.B. the mapping to a dictionary won't work with multiple headers
                     connection.responseHeaders[hk]=hv
            output.write(data)
            output.flush()

        def start_response(status,response_headers,exc_info=None):
            if exc_info:
                try:
                    if headers_sent:
                        # Re-raise original exception if headers sent
                        raise exc_info[0], exc_info[1], exc_info[2]
                finally:
                    exc_info = None     # avoid dangling circular ref
            elif headers_set:
                raise AssertionError("Headers already set!")
                
            headers_set[:] = [status,response_headers]
            return write

        result = self.application(environ, start_response)
        try:
            for data in result:
                if data:    # don't send headers until body appears
                    write(data)
            if not headers_sent:
                write('')   # send headers now if body was empty
        finally:
            if hasattr(result,'close'):
                result.close()
                
        return connection.response()
