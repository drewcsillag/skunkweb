# Time-stamp: <02/02/15 00:03:34 smulloni>
# $Id$

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

Configuration.mergeDefaults(rewriteRules = [],
                            rewriteApplyAll = 1,
                            rewriteMatchToArgs=1)

PreRewriteMatch=Hook()
PostRewriteMatch=Hook()
PreRewrite=Hook()
PostRewrite=Hook()
PreRewriteCleanup=Hook()

_sre_pattern_type=type(re.compile('foo'))

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
            pat=re.compile(rule[0])
        
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
            connection.uri = m.expand(rule[1])
            groupdict=m.groupdict()
            if Configuration.rewriteMatchToArgs:
                connection.args.update(groupdict)
            sessionDict['rewriteRules'][key].update(groupdict)
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
# $Log$
########################################################################
