# Time-stamp: <02/09/27 15:25:28 smulloni>
# $Id$

"""
a module for serving XMLRPC from SkunkWeb.
"""
import pydoc
import re
import sys
import xmlrpclib

class XMLRPCException(Exception): pass

_tdoc=pydoc.TextDoc()

def _methodSignature(server, method):
    func=server.get_func(method)
    if func:
        s=pydoc.plain(_tdoc.docroutine(func))
        s=re.subn(func.__name__, method, s, 1)
        return s
    raise XMLRPCException, "no such method: %s" % method

def _methodHelp(server, method):
    func=server.get_func(method)
    if func:
        return server.funcs[method][1]
    raise XMLRPCException, "no such method: %s" % method


class XMLRPCServer:
    def __init__(self, add_system_methods=1):
        self.funcs={}
        if add_system_methods:
            self.register_function(self.funcs.keys,
                                   'system.listMethods')
            self.register_function(lambda x: _methodSignature(self, x),
                                   'system.methodSignature')
            self.register_function(lambda x: _methodHelp(self, x),
                                   'system.methodHelp')

    def register_function(self,
                          func,
                          name=None,
                          docstring=None):
        if name is None:
            name=func.__name__
        if docstring is None:
            docstring=func.__doc__ or ""
        self.funcs[name]=(func, docstring)

    def get_func(self, funcname):
        if self.funcs.has_key(funcname):
            return self.funcs[funcname][0]

    def handle(self, connection):
        """
        connection should be a web.protocol.HttpConnection object.
        """
        if connection.method!='POST':
            raise XMLRPCException, "precondition violated: not an HTTP POST"
        params, method=xmlrpclib.loads(connection._stdin)
        try:
            f=self.get_func(method)
            if not f:
                raise XMLRPCException, "method not supported: %s" % method
            res=(f(*params),)
            have_response=1
        except:
            have_response=None            
            res=xmlrpclib.Fault(1, "%s:%s" % (sys.exc_type, sys.exc_value))
            
        connection.setStatus(200)
        connection.responseHeaders['Content-type']='text/xml'
        return xmlrpclib.dumps(res, methodresponse=have_response)        
