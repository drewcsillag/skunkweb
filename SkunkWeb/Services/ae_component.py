#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
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
    from SkunkWeb import Configuration, confvars
    # set our defaults from AE defaults
    Configuration.mergeDefaults(
        documentRoot = confvars.DEFAULT_DOCROOT,
        compileCacheRoot = confvars.DEFAULT_CACHE, 
        componentCacheRoot = confvars.DEFAULT_CACHE,
        failoverComponentCacheRoot = "%s/failoverCache" % Configuration.SkunkRoot,
        mimeTypesFile = confvars.DEFAULT_MIME_TYPES_FILE_NAME,
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
    __checkScopes(Configuration.scopeMatchers())

def __checkScopes(m):
    from SkunkWeb import Configuration
    #if no compileCacheRoot, don't need to check scoped stuff
    # BUG ... the absence of compileCacheRoot at the top level
    # doesn't mean that it isn't defined somewhere else....
    # FIXME
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
    global DEBUG, ERROR, COMPONENT, Component
    try:
        DEBUG
    except:
        from SkunkWeb.LogObj import ERROR, DEBUG
    try:
        COMPONENT
    except:
        from SkunkWeb.ServiceRegistry import COMPONENT
    try:
        Component
    except:
        from AE import Component
    sargs = argDict.copy()
    out, exp = _savedRealRenderComponent(name, argDict, auxArgs, compType,
                                         srcModTime)

    #if not a textual component, we have no business being here
    if compType not in (Component.DT_REGULAR, Component.DT_INCLUDE):
        DEBUG(COMPONENT, 'not a textual component')
        return out, exp

    from SkunkWeb import Configuration
    ccl = Configuration.componentCommentLevel
    if ccl <= 0:
        DEBUG(COMPONENT, 'ccl not > 0')
        return out, exp
    
    if len(Component.componentStack):
        tlns = Component.componentStack[ 0 ].namespace
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

