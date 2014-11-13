# Time-stamp: <03/02/08 09:37:03 smulloni>

"""
a module for serving XMLRPC from SkunkWeb.
"""
# for basic auth support
from __future__ import nested_scopes
import pydoc
import os
import re
import sys
import xmlrpclib

_tdoc=pydoc.TextDoc()

# These constants, and the multicall implementation below,
# are based on code by Eric Kidd.  Python 2.3 should have
# this constants in xmlrpclib, too.  Other code is derived
# from the standard library's SimpleXMLRPCServer.py, and
# from a cgi script by Fredrik Lundh.

INTERNAL_ERROR = -500
TYPE_ERROR = -501
INDEX_ERROR = -502
PARSE_ERROR = -503
NETWORK_ERROR = -504
TIMEOUT_ERROR = -505
NO_SUCH_METHOD_ERROR = -506
REQUEST_REFUSED_ERROR = -507
INTROSPECTION_DISABLED_ERROR = -508
LIMIT_EXCEEDED_ERROR = -509
INVALID_UTF8_ERROR = -510

# Some type names for use in method signatures;
# this is borrowed from Eric Kidd's code in xmlrpc-c's
# xmlrpc_registry.py.
INT="int"
BOOLEAN="boolean"
DOUBLE="double"
STRING="string"
DATETIME="dateTime.iso8601"
BASE64="base64"
ARRAY="array"
STRUCT="struct"
UNDEF="undef"

_multicall_doc="""
Processes an array of calls, and return an array of results.  Calls
should be structs of the form {'methodName': string, 'params': array}.
Each result will either be a single-item array containg the result
value, or a struct of the form {'faultCode': int, 'faultString': string}.
This is useful when you need to make lots of small calls without lots of
round trips.  -- [from Eric Kidd's implementation, upon which this is
based]
""".strip()

class XMLRPCServer:
    def __init__(self, add_system_methods=1, max_request=50000):
        self.funcs={}
        self.max_request=max_request
        if add_system_methods:
            self.register_function(self.funcs.keys,
                                   'system.listMethods',
                                   'Lists the names of registered methods',
                                   [[ARRAY]])
            # using lambdas to keep the pydoc method signature accurate
            self.register_function(lambda method: self._methodSignature(method),
                                   'system.methodSignature',
                                   ('Returns the signature of method requested.  '\
                                    'Raises a Fault if the method does not exist'),
                                   [[ARRAY, STRING]])
            self.register_function(lambda method: self._methodHelp(method),
                                   'system.methodHelp',
                                   ("Gives help for the method requested.  "\
                                   "Raises a Fault if the method does not exist."),
                                   [[STRING, STRING]])

            self.register_function(lambda calls: self._multicall(calls),
                                   'system.multicall',
                                   _multicall_doc,
                                   [[ARRAY, ARRAY]])

            self.register_function(lambda method: self._methodPydoc(method),
                                   'system.methodPydoc',
                                   ('Gives pydoc method signature for the method requested.  '\
                                    'Raises a Rault if the method does not exist.'),
                                   [[STRING]])

    def _methodPydoc(self, method):
        func=self.get_func(method)
        if func:
            s=pydoc.plain(_tdoc.docroutine(func)).strip()
            # remove the docstring
            cr=s.find('\n')
            if cr!=-1:
                s=s[:cr]
            # rename the method, if needed
            fname=func.__name__
            # this is a workaround for a pydoc bug
            # that will probably be fixed one day....
            if fname=='<lambda>':
                fname='lambda'
                s=re.sub(fname, method+'(', s, 1)+')'
                
            elif method != fname:
                s=re.sub(fname, method, s, 1)
            s=re.sub(r'\.\.\.', '', s)
            return s
        raise xmlrpclib.Fault(NO_SUCH_METHOD_ERROR, method)

    def _methodSignature(self, method):
        fspec=self.funcs.get(method)
        if not fspec or fspec[-1] is None:
            raise xmlrpclib.Fault(NO_SUCH_METHOD_ERROR, method)
        return fspec[-1]
            

    def _methodHelp(self, method):
        func=self.get_func(method)
        if func:
            return self.funcs[method][1]
        raise xmlrpclib.Fault(NO_SUCH_METHOD_ERROR, method)

    def _multicall (self, calls):
        results = []
        for call in calls:
            try:
                name = call['methodName']
                params = call['params']
                if name == 'system.multicall':
                    errmsg = "Recursive system.multicall forbidden"
                    return xmlrpclib.Fault(REQUEST_REFUSED_ERROR, errmsg)
                result = [self.dispatch(name, params)]
            except xmlrpclib.Fault, fault:
                result = {'faultCode': fault.faultCode,
                          'faultString': fault.faultString}
            except:
                errmsg = "%s:%s" % (sys.exc_type, sys.exc_value)
                result = {'faultCode': 1, 'faultString': errmsg}
            results.append(result)
        return results            

    def register_function(self,
                          func,
                          name=None,
                          docstring=None,
                          signature=UNDEF):
        if name is None:
            name=func.__name__
        if docstring is None:
            docstring=func.__doc__ or ""
        self.funcs[name]=(func, docstring.strip(), signature)

    def get_func(self, funcname):
        if self.funcs.has_key(funcname):
            return self.funcs[funcname][0]

    def dispatch(self, methodname, params):
        try:
            f=self.get_func(methodname)
            if not f:
                return xmlrpclib.Fault(NO_SUCH_METHOD_ERROR,
                                      methodname)
            return (f(*params),)
        except xmlrpclib.Fault, r:
            return r
        except:
            return xmlrpclib.Fault(1,
                                   "%s: %s" % (sys.exc_type,
                                               sys.exc_value))

    def handle_cgi(self, giveup=None):
        """
        for use in a cgi script.  If supplied, giveup should be
        a function with one required argument (message) and one optional
        (status).
        """
        if not giveup:
            def giveup(message, status=400):
                print "Status: %d" % status
                print
                print message
                sys.exit(0)
        
        if os.environ.get('REQUEST_METHOD')!='POST':
            giveup("precondition violated: not an HTTP POST")
        if self.max_request > 0:
            bytelen=int(os.environ.get("CONTENT_LENGTH", 0))
            if bytelen > self.max_request:
                # perhaps I should return a LIMIT_EXCEEDED fault instead?
                giveup("request too large", 413)
            
        params, method=xmlrpclib.loads(sys.stdin.read(bytelen))
        result=self.dispatch(method, params)
        mres=not isinstance(result, xmlrpclib.Fault)
        response=xmlrpclib.dumps(result, methodresponse=mres)
        
        print "Content-Type: text/xml"
        print "Content-Length: %d" % len(response)
        print
        print response


    def handle(self, connection):
        """
        connection should be a web.protocol.HttpConnection object
        (SkunkWeb only, presumably)
        """
        if connection.method!='POST':
            raise xmlrpclib.Fault(REQUEST_REFUSED_ERROR,
                                  "precondition violated: not an HTTP POST")
        if self.max_request > 0 and len(connection._stdin) > self.max_request:
            # see note in handle_cgi about returning a fault
            connection.setStatus(413)
            connection.responseHeaders['Content-type']='text/plain'
            return "request too large"
        params, method=xmlrpclib.loads(connection._stdin)
        res=self.dispatch(method, params)
        connection.setStatus(200)
        connection.responseHeaders['Content-type']='text/xml'
        mres=not isinstance(res, xmlrpclib.Fault)
        return xmlrpclib.dumps(res, methodresponse=mres)


def munge_transports():
    """
    dynamically patches the transport and ServerProxy objects
    so you can add arbitrary HTTP headers to an xmlrpc request,
    like so:
       s=ServerProxy('/whatever/')
       s.transport.more_headers={'X-Doo-Hickey' : 'Fruit Loops'}
    Hopefully, Python 2.3 will not require this brutal hack.
    """
    _old_send_request=xmlrpclib.Transport.send_request
    def send_request(self, connection, handler, request_body):
        _old_send_request(self, connection, handler, request_body)
        if hasattr(self, 'more_headers'):
            for k, v in self.more_headers.items():
                connection.putheader(k, v)
    xmlrpclib.Transport.send_request=send_request
    def get_transport(self):
        return self._ServerProxy__transport
    xmlrpclib.ServerProxy.get_transport=get_transport
            
        
    
