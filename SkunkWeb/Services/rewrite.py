# Time-stamp: <03/01/29 15:56:41 smulloni>
# $Id: rewrite.py,v 1.11 2003/01/28 22:01:42 smulloni Exp $

########################################################################
#  
#  Copyright (C) 2002, 2003 Andrew T. Csillag <drew_csillag@yahoo.com>,
#                           Jacob Smullyan <smulloni@smullyan.org>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
########################################################################

# graciously contributed by Spruce Weber <sprucely@hotmail.com>

from SkunkWeb import ServiceRegistry, Configuration, constants
ServiceRegistry.registerService('rewrite')
from SkunkWeb.LogObj import DEBUG, logException
from hooks import Hook
from SkunkWeb.ServiceRegistry import REWRITE
import re
import sys
from requestHandler.protocol import PreemptiveResponse

Configuration.mergeDefaults(rewriteBeforeScope=1,
                            rewriteRules = [],
                            rewriteApplyAll = 1,
                            rewriteMatchToArgs=1,
                            rewriteEnableHooks=0)

PreRewriteMatch=Hook()
PostRewriteMatch=Hook()
PreRewrite=Hook()
PostRewrite=Hook()
PreRewriteCleanup=Hook()

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
    def rewrite(self, match, connection, sessionDict, key):
        pass


class Redirect(DynamicRewriter):
    """
    redirects to another url upon a rewrite match.
    """
    def __init__(self, url_template):
        self.url_template=url_template

    def rewrite(self, match, connection, sessionDict, key):
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
    def rewrite(self, match, connection, sessionDict, key):
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

    def rewrite(self, match, connection, sessionDict, key):
        fs=Configuration.documentRootFS
        (path, info)=fs.split_extra(connection.uri)
        if not path:
            raise PreemptiveResponse, self.notFoundHandler(connection,
                                                           sessionDict)
        else:
            if self.add_info_to_args:
                connection.args[self.path_info_var_name]=info
            connection.requestHeaders['PATH_INFO']=info
            connection.uri= path


##class HostMatch(DynamicRewriter):
##    """
##    checks the Host header before doing any rewrite.
##    Superseded by RewriteCond.
##    """
##    def __init__(self,
##                 hostregex,
##                 replacement):
##        self.hostregex=_getcompiled(hostregex)
##        self.replacement=replacement

##    def rewrite(self, match, connection, sessionDict, key):
##        if self.hostregex.match(connection.host):
##            _dorewrite(match,
##                       connection,
##                       sessionDict,
##                       self.replacement,
##                       key)
    
class RewriteCond:
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
        self.unixPath=unixpath
        self.port=port
        self.skunkPort=skunkPort
        self.ip=ip

    def __call__(connection, sessionDict):
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
                if (not t) or not getcompiled(pat).search(t):
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

def _dorewrite(match, connection, sessionDict, replacement, key):
    if hasattr(replacement, 'rewrite'):
        replacement.rewrite(match, connection, sessionDict, key)
    else:
        if callable(replacement):
            connection.uri=match.re.sub(replacement, connection.uri)
        else:
            connection.uri=match.expand(replacement)
        groupdict=match.groupdict()
        if groupdict:
            if Configuration.rewriteMatchToArgs:
                connection.args.update(groupdict)
            if Configuration.rewriteEnableHooks:
                sessionDict['rewriteRules'][key].update(groupdict)


def _dorewriteloop(connection, sessionDict, rules):
    for p, r in rules:
        if callable(p):
            if p(connection, sessionDict):
                _dorewriteloop(connection, sessionDict, r)
        else:
        m = _getcompiled(p).search(connection.uri)
        if m is not None:
            if Configuration.rewriteEnableHooks:
                key=(p, r)
                sessionDict['rewriteRules'][key] = {}
                sessionDict['rewriteCurrentRule'] = key
                try:
                    DEBUG(REWRITE, 'executing PreRewrite hook')
                    PreRewrite(connection, sessionDict)
                    DEBUG(REWRITE, 'survived PreRewrite hook')
                except:
                    logException()

            _dorewrite(m, connection, sessionDict, r, key)

            if Configuration.rewriteEnableHooks:
                try:
                    DEBUG(REWRITE, 'executing PostRewrite hook')
                    PostRewrite(connection, sessionDict)
                    DEBUG(REWRITE, 'survived PostRewrite hook')
                except:
                    logException()
                try:
                    del sessionDict['rewriteCurrentRule']
                except KeyError:
                    pass
            if not Configuration.rewriteApplyAll:
                break
    
        
def _rewritePre(connection, sessionDict):
    """
    hook for web.protocol.PreHandleConnection
    """
    if Configuration.rewriteEnableHooks:
        sessionDict['rewriteRules'] = {}
        try:
            DEBUG(REWRITE, 'executing PreRewriteMatch hook')
            PreRewriteMatch(connection, sessionDict)
            DEBUG(REWRITE, 'survived PreRewriteMatch hook')
        except:
            logException()
    rules = Configuration.rewriteRules
    if Configuration.rewriteEnableHooks:
        if sessionDict.has_key('rewriteAddRules'):
            for newRule in sessionDict['rewriteAddRules']:
                # optional 3rd element in tuple specifies index
                # for placement in rules
                if len(newRule) > 2 and newRule[2] <= len(rules):
                    rules.insert(newRule[2], newRule[:2])
                else:
                    rules.append(newRule)
    _dorewriteloop(connection, sessionDict, rules)
    

def _rewritePost(requestData, sessionDict):
    """
    hook for requestHandler.requestHandler.CleanupRequest
    """
    if Configuration.rewriteEnableHooks:
        try:
            DEBUG(REWRITE, 'executing PreRewriteCleanup hook')
            PreRewriteCleanup(requestData, sessionDict)
            DEBUG(REWRITE, 'survived PreRewriteCleanup hook')
        except:
            logException()
        try:
            del sessionDict['rewriteRules']
        except KeyError:
            pass


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
    rh.CleanupRequest.addFunction(_rewritePost, jobGlob)

__initHooks()


