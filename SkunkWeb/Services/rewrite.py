# Time-stamp: <02/05/21 21:30:25 smulloni>
# $Id: rewrite.py,v 1.4 2002/05/10 18:05:12 smulloni Exp $

########################################################################
#  
#  Copyright (C) 2002 Andrew T. Csillag <drew_csillag@yahoo.com>,
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

from SkunkWeb import ServiceRegistry, Configuration
ServiceRegistry.registerService('rewrite')
from SkunkWeb.LogObj import DEBUG, logException
from hooks import Hook
from SkunkWeb.ServiceRegistry import REWRITE
import re
import sys
from requestHandler.protocol import PreemptiveResponse

Configuration.mergeDefaults(rewriteRules = [],
                            rewriteApplyAll = 1,
                            rewriteMatchToArgs=1)

PreRewriteMatch=Hook()
PostRewriteMatch=Hook()
PreRewrite=Hook()
PostRewrite=Hook()
PreRewriteCleanup=Hook()

_sre_pattern_type=type(re.compile('foo'))

_patdict={}

def _getcompiled(regexstring):
    if not _patdict.has_key(regexstring):
        pat=re.compile(regexstring)
        _patdict[regexstring]=pat
        return pat
    return _patdict[regexstring]

########################################################################

class DynamicRewriter:
    def refresh(self, connection, sessionDict):
        self.connection=connection
        self.sessionDict=sessionDict

    def __call__(self, match):
        """
        by default, does nothing;
        override this to do something else
        """
        return match.string

class Redirect(DynamicRewriter):
    """
    redirects to another url upon a rewrite match.
    """
    def __init__(self, url_template):
        self.url_template=url_template

    def __call__(self, match):
        url=match.expand(self.url_template)
        self.connection.redirect(url)
        raise PreemptiveResponse, self.connection.response()

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
    def __call__(self, match):
        raise PreemptiveResponse, self.handler(
            self.connection,
            self.sessionDict)


########################################################################

def _dorewrite(match, connection, sessionDict, replacement, key):
    if callable(replacement):
        if isinstance(replacement, DynamicRewriter):
            replacement.refresh(connection, sessionDict)
        connection.uri = match.re.sub(replacement, connection.uri)
    else:
        connection.uri = match.expand(replacement)
    groupdict=match.groupdict()
    if Configuration.rewriteMatchToArgs:
        connection.args.update(groupdict)
    sessionDict['rewriteRules'][key].update(groupdict)


def _rewritePre(connection, sessionDict):
    """
    hook for web.protocol.PreHandleConnection
    """
    sessionDict['rewriteRules'] = {}
    try:
        DEBUG(REWRITE, 'executing PreRewriteMatch hook')
        PreRewriteMatch(connection, sessionDict)
        DEBUG(REWRITE, 'survived PreRewriteMatch hook')
    except:
        logException()
    rules = Configuration.rewriteRules
    if sessionDict.has_key('rewriteAddRules'):
        for newRule in sessionDict['rewriteAddRules']:
            #optional 3rd element in tuple specifies index
            #for placement in rules
            if len(newRule) > 2 and newRule[2] <= len(rules):
                rules.insert(newRule[2], newRule[:2])
            else:
                rules.append(newRule)
    for rule in rules:
        if type(rule[0])==_sre_pattern_type:
                pat=rule[0]
        else:
            pat=_getcompiled(rule[0])
        
        m = pat.search(connection.uri)
        if m != None:
            key=(rule[0], rule[1])
            sessionDict['rewriteRules'][key] = {}
            sessionDict['rewriteCurrentRule'] = key
            try:
                DEBUG(REWRITE, 'executing PreRewrite hook')
                PreRewrite(connection, sessionDict)
                DEBUG(REWRITE, 'survived PreRewrite hook')
            except:
                logException()

            _dorewrite(m, connection, sessionDict, rule[1], key)
            
            try:
                DEBUG(REWRITE, 'executing PostRewrite hook')
                PostRewrite(connection, sessionDict)
                DEBUG(REWRITE, 'survived PostRewrite hook')
            except:
                logException()
            del sessionDict['rewriteCurrentRule']
            if not Configuration.rewriteApplyAll: break

def _rewritePost(requestData, sessionDict):
    """
    hook for requestHandler.requestHandler.CleanupRequest
    """
    try:
        DEBUG(REWRITE, 'executing PreRewriteCleanup hook')
        PreRewriteCleanup(requestData, sessionDict)
        DEBUG(REWRITE, 'survived PreRewriteCleanup hook')
    except:
        logException()
    del sessionDict['rewriteRules']

def __initHooks():
    import web.protocol as wp
    import SkunkWeb.constants as sc
    import requestHandler.requestHandler as rh
    jobGlob="%s*" % sc.WEB_JOB
    wp.PreHandleConnection.addFunction(_rewritePre, jobGlob)
    rh.CleanupRequest.addFunction(_rewritePost, jobGlob)

__initHooks()

########################################################################
# $Log: rewrite.py,v $
# Revision 1.4  2002/05/10 18:05:12  smulloni
# added a rewriter that returns a 404.
#
# Revision 1.3  2002/05/01 21:32:37  smulloni
# fixing typos and goofs
#
# Revision 1.2  2002/04/27 19:28:48  smulloni
# implemented dynamic rewriting in rewrite service; fixed Include directive.
#
# Revision 1.1  2002/02/15 05:08:39  smulloni
# added Spruce Weber's rewrite service.
#
########################################################################
