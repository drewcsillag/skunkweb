#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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
# $Id: ae_component.py,v 1.8 2001/07/30 16:07:29 smulloni Exp $
# Time-stamp: <01/05/04 11:27:17 smulloni>
########################################################################

"""
A service used by remote and templating that initializes the AE component
facilities.  It adds global hooks from AE.cfg. and a hook to requestHandler's
PostRequest hook.
"""

def __initFlags():
    from SkunkWeb.ServiceRegistry import registerService
    registerService('ae_component')

def __initDebug():
    from SkunkWeb import LogObj
    from AE import Logs
    # replace AE's log stuff with ours, first methods:
    for name in ['DEBUGIT', "DEBUG", "LOG", "ACCESS", "ERROR"]:
        setattr(Logs, name, getattr(LogObj, name))
    # then debug flags:
    from SkunkWeb import ServiceRegistry 
    for name in ['COMPONENT',
                 'COMPONENT_TIMES',
                 'MEM_COMPILE_CACHE',
                 'CACHE',
                 'WEIRD',
                 'COMPONENT_TTL']:
        setattr(Logs, name, getattr(ServiceRegistry, name))

def __initConfig():
    from AE import cfg
    from SkunkWeb import Configuration
    # set our defaults from AE defaults
    Configuration.mergeDefaults(
        documentRoot = "%s/docroot" % Configuration.SkunkRoot,
        compileCacheRoot = "%s/cache" % Configuration.SkunkRoot,
        componentCacheRoot = "%s/cache" % Configuration.SkunkRoot,
        failoverComponentCacheRoot = "%s/failoverCache" % Configuration.SkunkRoot,
        mimeTypesFile = "%s/etc/mime.types" % Configuration.SkunkRoot,
        componentCommentLevel = 0,
        )
    dd = {}
    for k, v in cfg.Configuration._d.items():
        if k not in ['documentRoot',
                     'compileCacheRoot',
                     'componentCacheRoot',
                     'failoverComponentCacheRoot',
                     'mimeTypesFile',
                     'componentCommentLevel']:
            dd[k]=v
    Configuration.mergeDefaults(dd)
            
    # set AE's config object to ours
    cfg.Configuration = Configuration
    __checkScopes(Configuration.matchers)

def __checkScopes(m):
    from SkunkWeb import Configuration
    #if no compileCacheRoot, don't need to check scoped stuff
    if not Configuration.compileCacheRoot:
        return 
    for i in m:
        #check to see that if 
        if i.overlayDict.has_key('documentRoot'):
            if not i.overlayDict.has_key('compileCacheRoot') or \
               i.overlayDict['compileCacheRoot'] == \
               Configuration.compileCacheRoot:
                import SkunkExcept
                raise SkunkExcept.SkunkStandardError(
                    'cannot set documentRoot (to %s) in a Scope declaration'
                    ' without setting compileCacheRoot or setting it to'
                    ' something different than the global setting (%s)' % (
                    i.overlayDict['documentRoot'],
                    Configuration.compileCacheRoot))
        __checkScopes(i.children())

def __initHooks():
    from AE import cfg, Component
    from SkunkWeb import Hooks, constants
    # TEMPORARILY REMOVED
    #constants.AE_COMPONENT_JOB='/ae_component/'
    from requestHandler.requestHandler import PostRequest
    Hooks.ServerStart.append(cfg.serverInit)
    Hooks.ChildStart.append(cfg.childInit)
    jobGlob='*%s*' % constants.AE_COMPONENT_JOB
    PostRequest.addFunction(Component._postRequestRenderer, jobGlob)
    PostRequest.addFunction(_cleanupComponentStack, jobGlob)

    global _savedRealRenderComponent
    _savedRealRenderComponent = Component._realRenderComponent
    Component._realRenderComponent = _componentCommentRenderComponent
    
def _cleanupComponentStack(*args):
    import AE.Component
    AE.Component.resetComponentStack()


def _trapClose(s):
    return s.replace('--', '- -')

def _componentCommentRenderComponent(
    name, argDict, auxArgs, compType, srcModTime ):
    import AE.Component
    from SkunkWeb.LogObj import ERROR, DEBUG
    from SkunkWeb.ServiceRegistry import COMPONENT

    sargs = argDict.copy()
    out, exp = _savedRealRenderComponent(name, argDict, auxArgs, compType,
                                         srcModTime)

    #if not a textual component, we have no business being here
    if compType not in (AE.Component.DT_REGULAR, AE.Component.DT_INCLUDE):
        DEBUG(COMPONENT, 'not a textual component')
        return out, exp

    from SkunkWeb import Configuration
    ccl = Configuration.componentCommentLevel
    if ccl <= 0:
        DEBUG(COMPONENT, 'ccl not > 0')
        return out, exp
    
    if len(AE.Component.componentStack):
        tlns = AE.Component.componentStack[ 0 ].namespace
        #if not an html page, we shouldn't comment then either
        if not tlns['CONNECTION'].responseHeaders.get(
            'Content-Type') == 'text/html':
            DEBUG(COMPONENT, 'not an html page')
            return out, exp
    else: #component stack is for some reason empty
        DEBUG(COMPONENT, 'component stack is empty')
        return out, exp

    hdr = "<!-- component %s " % _trapClose(name)
    if Configuration.componentCommentLevel == 3:
        hdr += _trapClose(
            ' '.join(["%s=%s" % k for k in sargs.items()]))
    elif Configuration.componentCommentLevel == 2:
        hdr += _trapClose(
            ' '.join(['%s=...' %k for k in sargs.keys()]))
    #else: no argument commenting for level 1
        
    hdr += ' -->'
    trlr = '<!-- end component %s -->' % _trapClose(name)
    out = hdr + out + trlr
    return out, exp

__initDebug()
__initConfig()
__initHooks()

########################################################################
# $Log: ae_component.py,v $
# Revision 1.8  2001/07/30 16:07:29  smulloni
# made scope.Scopeable's "__matchers" field public: "matchers", and
# fixed two references to it, in ae_component and pars services.
#
# Revision 1.7  2001/07/29 15:29:31  drew
# made so cannot change docroot w/o changing the compileCacheRoot also
#
# Revision 1.6  2001/07/11 18:01:09  drew
# added component commenting, useful for debugging
#
# Revision 1.5  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.4  2001/05/04 18:38:47  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.3  2001/04/23 04:55:42  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.2  2001/04/16 18:10:16  smullyan
# fix to reload in Server.py; debug flags in AE module now reconciled with
# ServiceRegistry.
#
# Revision 1.1  2001/04/04 19:14:19  smullyan
# abstracted AE component initialization into the ae_component service;
# removed the equivalent functionality from templating_experimental,
# and modified templating_experimental and remote to import ae_component
# and invoke its hooks (by altering their jobNames).
#
########################################################################
