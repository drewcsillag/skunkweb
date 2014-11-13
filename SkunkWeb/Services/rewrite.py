# Time-stamp: <03/04/28 11:35:26 smulloni>

########################################################################
#  
#  Copyright (C) 2002, 2003 Andrew T. Csillag <drew_csillag@yahoo.com>,
#                           Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

# graciously contributed by Spruce Weber <sprucely@hotmail.com>

"""
The rewrite service is to SkunkWeb what mod_rewrite is to Apache;
it is used especially for rewriting urls, but can also be used to
make other changes to a request or how it is processed on the basis
of the url and other aspects of the connection.

In order to use the service, define ``Configuration.rewriteRules`` to be
a list of rewrite rules, which come in two forms::
 
    (<regular expression>, <replacement>)

or::
 
    (<rewrite condition>, [<more rules>])

In the first form, the regular expression is used to search
``CONNECTION.uri``.  If it matches, what happens next depends on what
kind of thing the replacement is.  If it has a method named
``rewrite``, that method is called, which can perform any action:
rewriting the url, altering the connection or the session dictionary
(which you can pretend you never heard about, as the best thing to do
is to leave it alone), raising a ``PreemptiveResponse`` and thus
handling the request, etc.  (A number of classes are provided that do
commonly needed things along these lines, like performing a redirect,
or returning a 404; and you can write your own.)  Else, if the
replacement is callable or a string, regular expression substitution
is performed on the original uri, and the result is assigned to
``CONNECTION.uri``.  An additional twist: if the regular expression
match contains a groupdict and ``Configuration.rewriteMatchToArgs`` is
true, then ``CONNECTION.args`` is updated with the groupdict.  This is
an easy way to use path info rather than querystrings to pass request
data to scripts.

In the second form, the first element must be callable with the
arguments ``(CONNECTION, sessionDict)`` (and again, you can ignore the
session dictionary).  If and only if it returns a true value, the
rules in the second element are executed.  A class is provided,
``rewrite.RewriteCond``, that performs most of the tests you'll want
to perform -- exactly the same tests as you would perform while
scoping.

By default, all of your rewrite rules will be applied, one by one.
But if you want it to stop after the first match, set
``Configuration.rewriteApplyAll`` to a false value.

This service used to contain a series of hooks and the ability
to use them to manipulate the list of rewrite rules at runtime.
These were relatively expensive and seemed to offer little functionality,
so they have been removed.
"""

from SkunkWeb import ServiceRegistry, Configuration, constants
ServiceRegistry.registerService('rewrite')
from SkunkWeb.LogObj import DEBUG, logException
from SkunkWeb.ServiceRegistry import REWRITE
import re
import sys
from requestHandler.protocol import PreemptiveResponse
from skunklib import normpath

def _fixPath(root, path):
    return normpath('%s/%s' % (root,path)) 

Configuration.mergeDefaults(rewriteBeforeScope=1,
                            rewriteRules = [],
                            rewriteApplyAll = 1,
                            rewriteMatchToArgs=1)

_sre_pattern_type=type(re.compile('foo'))

_patdict={}

def _getcompiled(regex):
    if type(regex)==_sre_pattern_type:
        _patdict.setdefault(regex.pattern, regex)
        return regex
    if not _patdict.has_key(regex):
        pat=re.compile(regex)
        _patdict[regex]=pat
        return pat
    return _patdict[regex]

########################################################################

class DynamicRewriter:
    def rewrite(self, match, connection, sessionDict): #, key):
        pass


class Redirect(DynamicRewriter):
    """
    redirects to another url upon a rewrite match.
    """
    def __init__(self, url_template):
        self.url_template=url_template

    def rewrite(self, match, connection, sessionDict):
        url=match.expand(self.url_template)
        connection.redirect(url)
        raise PreemptiveResponse, connection.response()

# use templating's 404 handler if it is already imported, 
# or is about to be loaded, to the extent possible to determine
if sys.modules.has_key('templating') \
       or 'templating' in Configuration.services:
    import templating
    fourOhFourHandler=templating.Handler.fourOhFourHandler

else:
    def fourOhFourHandler(connection, sessionDict):
        connection.setStatus(404)
        connection.responseHeaders['Content-Type']='text/html'
        connection.write(
            'Sorry the requested document (<tt>%s</tt>) is not available' \
            % connection.uri)
        return  connection.response()
    
class Status404(DynamicRewriter):
    """
    raises a 404 error
    """
    def __init__(self, handler=fourOhFourHandler):
        self.handler=handler
    def rewrite(self, match, connection, sessionDict):
        raise PreemptiveResponse, self.handler(connection,
                                               sessionDict)

class ExtraPathFinder(DynamicRewriter):
    """
    finds extra path info by walking up the supplied
    path until a non-directory file is found.  Returns
    a 404 if not found; otherwise, the url is rewritten
    to point to the existing resource, and a connection argument
    called (by default, but this may be changed with the
    "path_info_var_name" constructor argument)
    "path_info" is populated with the extra path info.
    """
    def __init__(self,
                 notFoundHandler=fourOhFourHandler,
                 add_info_to_args=1,
                 path_info_var_name='path_info',
                 ):
        self.notFoundHandler=notFoundHandler
        self.add_info_to_args=add_info_to_args
        self.path_info_var_name=path_info_var_name

    def rewrite(self, match, connection, sessionDict): 
        fs=Configuration.documentRootFS
        (path, info)=fs.split_extra(_fixPath(Configuration.documentRoot, connection.uri))
        if not path:
            raise PreemptiveResponse, self.notFoundHandler(connection,
                                                           sessionDict)
        else:
            if self.add_info_to_args:
                connection.args[self.path_info_var_name]=info
            connection.requestHeaders['PATH-INFO']=info
            connection.uri= path[len(Configuration.documentRoot):]


class RewriteCond:
    """
    as the first element in a rewrite rule tuple, 
    """
    def __init__(self,
                 uri=None,
                 host=None,
                 unixPath=None,
                 port=None,
                 skunkPort=None,
                 ip=None,
                 ):
        self.uri=uri 
        self.host=host
        self.unixPath=unixPath
        self.port=port
        self.skunkPort=skunkPort
        self.ip=ip

    def __call__(self, connection, sessionDict):
        for pat, target in zip((self.uri,
                                self.host,
                                self.unixPath,
                                self.ip),
                               (constants.LOCATION,
                                constants.HOST,
                                constants.UNIXPATH,
                                constants.IP)):
            if pat is not None:
                t=sessionDict.get(target)
                if not t:
                    return 0
                if callable(pat):
                    return pat(t)
                elif not _getcompiled(pat).search(t):
                    return 0
        for pat, target in zip((self.port,
                                self.skunkPort),
                               (constants.SERVER_PORT,
                                constants.PORT)):
            if pat is not None:
                t=sessionDict.get(target)
                if not t:
                    return 0
                if callable(pat):
                    if not pat(t):
                        return 0
                elif pat!=t:
                    return 0

        return 1
        
        
########################################################################

def _dorewrite(match, connection, sessionDict, replacement): 
    if hasattr(replacement, 'rewrite'):
        replacement.rewrite(match, connection, sessionDict)
    else:
        if callable(replacement):
            connection.uri=match.re.sub(replacement, connection.uri)
        else:
            connection.uri=match.expand(replacement)
        groupdict=match.groupdict()
        if groupdict:
            if Configuration.rewriteMatchToArgs:
                connection.args.update(groupdict)

def _dorewriteloop(connection, sessionDict, rules):
    for p, r in rules:
        if callable(p):
            if p(connection, sessionDict):
                _dorewriteloop(connection, sessionDict, r)
            continue

        m = _getcompiled(p).search(connection.uri)
        if m is not None:

            _dorewrite(m, connection, sessionDict, r)

            if not Configuration.rewriteApplyAll:
                break
    
        
def _rewritePre(connection, sessionDict):
    """
    hook for web.protocol.PreHandleConnection
    """
    rules = Configuration.rewriteRules
    _dorewriteloop(connection, sessionDict, rules)
    
def __initHooks():
    import web.protocol as wp
    import SkunkWeb.constants as sc
    import requestHandler.requestHandler as rh
    jobGlob="%s*" % sc.WEB_JOB
    if Configuration.rewriteBeforeScope:
        hook=wp.HaveConnection
    else:
        hook=wp.PreHandleConnection
    hook.addFunction(_rewritePre, jobGlob)

__initHooks()


