#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
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
# $Id: Component.py,v 1.4 2001/08/27 18:29:21 drew_csillag Exp $
# Time-stamp: <2001-07-10 12:20:38 drew>
########################################################################

import os
import time

from SkunkExcept import *
from DT import DT_REGULAR, DT_DATA, DT_INCLUDE

import Error
import Cache
import Executables
# ??? reconcile this with other changes to debug system
from Logs import COMPONENT, COMPONENT_TIMES, DEBUG, ACCESS, DEBUGIT
from Logs import COMPONENT_TTL

# ??? reconcile this with ConfigLoader.Config
import cfg

#config vars
cfg.Configuration._mergeDefaultsKw(
#    defaultDefer = 0, 
    defaultExpiryDuration = 30,
    fallbackToCache = None,
)
#/config

_postRequestRenderList = []
_doingDeferred = 0
componentStack = []
topOfComponentStack = -1

globalNamespace = {}
autoVariables = {} # name: default_value
componentHandlers={}

def resetComponentStack():
    global topOfComponentStack
    componentStack[:] = []
    topOfComponentStack = -1
    
class ComponentStackFrame:
    def __init__(self, name, namespace, executable, argDict, auxArgs,
                 compType ):
        self.name = name
        self.namespace = namespace
        self.executable = executable
        self.argDict = argDict
        self.auxArgs = auxArgs
        self.compType = compType

    def __del__(self):
        if self.compType != DT_INCLUDE:
            for k in self.namespace.keys():
                self.namespace[k] = None
            self.namespace.clear()

def strBool(s):
    s = str(s)
    if s.lower() in ('yes','true', '1', 't', 'y'):
        return 1
    return 0

NO, YES, DEFER, FORCE, OLD = range(5)
def strCache(s):
    s = str(s)
    s = s.lower()
    DEBUG(COMPONENT, 's is %s' % s)
    if s in ('yes','true', '1', 't', 'y'):
        return YES
    elif s in ('defer', '2'):
        return DEFER
    elif s in ('force', '3'):
        return FORCE
    elif s in ('old', '4'):
        return OLD
    return NO

class ComponentHandler:
    """
    interface for a
    pluggable component handler
    """
    def callComponent(self,
                      callProtocol,
                      name,
                      argDict,
                      cache,
                      compType,
                      srcModTime):
        raise NotImplementedError

class DefaultComponentHandler(ComponentHandler):

    def callComponent (self,
                       callProtocol,
                       name,
                       argDict, 
                       cache,
                       compType,
                       srcModTime):

        #if cache and not cache == DEFER:
        #    #if defer is None or defer == -1:
        #    cache = cfg.Configuration.defaultDefer and DEFER or cache
        #DEBUG(COMPONENT, "callComponent %s %s" % (name, cache))

        name = _rectifyRelativeName(name)
        
        # get auto arguments that weren't explicitly passed
        if compType != DT_INCLUDE:
            auxArgs = _getAuxArgs(argDict)
        else:
            # check for programmer stupidities
            if argDict != {}:
                raise SkunkStandardError, "called include with arguments!?!?!"
            auxArgs = {}
            if cache:
                raise SkunkStandardError, "cannot call include with cache enabled"

        if not cache:
            #DEBUG(COMPONENT, "call _render")
            ACCESS("rendering %s" % name)
            return _renderComponent(name, argDict, auxArgs, compType), 1, 0

        # cache is true
        #DEBUG(COMPONENT, "cache is true")
    
        # will return None if src modtime is different than stored in component    
        mashed = argDict.copy()
        mashed.update(auxArgs)
        cached, srcModTime = Cache.getCachedComponent(name,
                                                      mashed,
                                                      srcModTime)

        if not cached or cache == FORCE: # cache not available, or ignored
            #if cache == FORCE:
            #    DEBUG(COMPONENT, 'cache is force')
            #else:
            #    DEBUG(COMPONENT, "cache not available -- cached=%s" % cached)
            # render
            ACCESS("rendering %s (cache=yes)" % name)
            return _renderComponentAndCache(name,
                                            argDict,
                                            auxArgs,
                                            compType,
                                            srcModTime,
                                            cached ), 1, 0

        # cache is available
        #DEBUG(COMPONENT, "cache available")

        if cached.valid or cache == OLD: # cache not expired?
            #if cache == OLD:
            #    DEBUG(COMPONENT, 'cache %s, specified OLD'  % (
            #        cached.valid and 'ok' or 'expired'))
            #else: #cache is valid anyway
            #    DEBUG(COMPONENT, "cache ok, using it")
            #    if DEBUGIT(COMPONENT_TTL):
            #        DEBUG(COMPONENT_TTL, "component %s" % name)
            #        if cached.ttl >= 3600:
            #            h = int(cached.ttl / 3600)
            #            ttl = cached.ttl - h*3600
            #            m = int(ttl / 60)
            #            s = ttl - m*60
            #            DEBUG(COMPONENT_TTL, "ttl %sh %sm %ss" % (h, m, s))
            #        elif cached.ttl >= 60:
            #            ttl = cached.ttl
            #            m = int(ttl / 60)
            #            s = ttl - m*60
            #            DEBUG(COMPONENT_TTL, "ttl %sm %ss" % (m, s))
            #        else:
            #            DEBUG(COMPONENT_TTL, "ttl %ss" % cached.ttl)
            ACCESS("using cached form of %s" % name)
            if cached.valid:
                expired = 0
            else:
                expired = 1
            return cached.out, 0, expired

        # cache is available but has expired
        #DEBUG(COMPONENT, "cache expired")

        if not (cache == DEFER) or _doingDeferred: # non-deferred execution?
            ACCESS("rendering %s (cache=yes)" % name)
            #if not (cache == DEFER):
            #    DEBUG(COMPONENT, "not deferred, rendering and caching")
            #else:
            #    DEBUG(COMPONENT,
            #          "defer request overridden, rendering and caching now")
            # render and cache
            return _renderComponentAndCache(name,
                                            argDict,
                                            auxArgs,
                                            compType,
                                            srcModTime,
                                            cached), 1, 1

        # deferred and cache is expired
        #DEBUG(COMPONENT, "deferred ttl was %s" % cached.ttl)
        if not cached.stale: # not stale? render after and return current
            #DEBUG(COMPONENT, "deferred and not stale, returning and rendering PF")
            ACCESS("using cached form of %s (cache=yes, defer=yes)" % name)
            mashed = argDict.copy()
            mashed.update(auxArgs)
            Cache.extendDeferredCachedComponent(name, mashed) 
            _renderPostRequestAndCache(name,
                                       argDict,
                                       auxArgs,
                                       compType,
                                       srcModTime,
                                       cached )
            return cached.out, 0, 1

        # deferred, cache expired and stale
        #DEBUG(COMPONENT, "deferred and stale, rendering")
        # render and cache
        ACCESS("rendering %s (cache=yes)" % name)
        return _renderComponentAndCache(name,
                                        argDict,
                                        auxArgs,
                                        compType,
                                        srcModTime,
                                        cached), 1, 1


defaultHandler=DefaultComponentHandler()

def callComponent (name, argDict, cache = 0,
                   compType = DT_REGULAR,
                   srcModTime = None):
    return fullCallComponent (name, argDict, cache, compType, srcModTime)[0]

def fullCallComponent (name, argDict, cache = 0,
                       compType = DT_REGULAR,
                       srcModTime = None):
    """calls component and returns (text, rendered, expired)
    rendered and expired are booleans
    """
    DEBUG(COMPONENT, "callComponent %s %s" % (name, compType))

    colonIndex=name.find("://")
    if colonIndex>0:
        callProtocol=name[:colonIndex]
        if componentHandlers.has_key(callProtocol):
            return componentHandlers[callProtocol].callComponent(callProtocol,
                                                                 name[3+colonIndex:],
                                                                 argDict,
                                                                 cache,
                                                                 compType,
                                                                 srcModTime)
    else:
        return defaultHandler.callComponent(None, name, argDict, cache, 
                                            compType, srcModTime)



def _rectifyRelativeName( name ):
    #if no previous components, or it's absolute, just return it as is
    if topOfComponentStack == -1:
        return '/' + name

    elif name[0] == '/':
        return name

    path, fname = os.path.split( componentStack[topOfComponentStack].name )
    return Cache._normpath("%s/%s" % (path, name))
    
def _renderPostRequestAndCache( name, argDict, auxArgs, compType, srcModTime,
                                cached ):
    _postRequestRenderList.append( (
        name, argDict, auxArgs, compType, srcModTime, cached) )
    
def _postRequestRenderer(*args):
    global _doingDeferred
    _doingDeferred = 1
    try:
        for name, argDict, auxArgs, compType, srcModTime, cached in \
            _postRequestRenderList:
            try:
                DEBUG(COMPONENT, 'deferredly rendering %s' % name)
                _renderComponentAndCache(
                    name, argDict, auxArgs, compType, srcModTime, cached )
            except:
                Error.logException()
        _postRequestRenderList[:] = []
    finally:
        _doingDeferred = 0
        
def _renderComponentAndCache( name, argDict, auxArgs, compType, srcModTime,
                              cached ):
    DEBUG(COMPONENT, '_renderComponentAndCache')
    try:
        mashed = argDict.copy()
        (out, cache_exp_time) = _realRenderComponent(
            name, argDict, auxArgs, compType, srcModTime )
        mashed.update(auxArgs)
        Cache.putCachedComponent(name, mashed, out, cache_exp_time)
    except:
        if cfg.Configuration.fallbackToCache and cached:
            DEBUG(COMPONENT, 'execution explosion and fallback active')
            Error.logException()
            DEBUG(COMPONENT, 'After logexc')
            return cached.out
        raise
            
    return out

def _realRenderComponent( name, argDict, auxArgs, compType, srcModTime ):
    global topOfComponentStack
    DEBUG(COMPONENT, "_realRenderComponent")
    executable = Executables.getExecutable( name, compType, srcModTime )

    if compType == DT_INCLUDE and componentStack:
        namespace = componentStack[topOfComponentStack].namespace
    else:
        namespace = globalNamespace.copy()

    namespace = executable.mergeNamespaces( namespace, argDict, auxArgs )

    componentStack.append( ComponentStackFrame(
        name, namespace, executable, argDict, auxArgs, compType ) )

    try:
        if DEBUGIT(COMPONENT_TIMES):
            beg = time.time()
        topOfComponentStack += 1
        out = executable.run()
    finally:
        topOfComponentStack -= 1
        if DEBUGIT(COMPONENT_TIMES):
            DEBUG(COMPONENT_TIMES, "execution of %s in %s" % (
                name, time.time() - beg))

    # normally this is equivalent to a pop, but if a component exception
    # was handled somewhere, we need to clean up the residual shit
    del componentStack[ topOfComponentStack+1 : ]

    expiration = namespace.get('__expiration',
                               time.time()
                               + cfg.Configuration.defaultExpiryDuration )
    
    if compType != DT_INCLUDE:
        #DEBUG(COMPONENT, 'clearing the namespace!!! %s %s' % (DT_INCLUDE, compType))
        namespace.clear()
        
    return out, expiration

def _renderComponent( name, argDict, auxArgs, compType ):
    DEBUG(COMPONENT, "call _realRender")
    return _realRenderComponent( name, argDict, auxArgs, compType, None )[0]

def _getAuxArgs( argDict ):
    ret = {}
    
    if componentStack:
        ns = componentStack[topOfComponentStack].namespace
    else:
        ns = globalNamespace

    for k, v in autoVariables.items():
        if not argDict.has_key( k ):
            ret[k] = ns.get(k, v)

    return ret

########################################################################
# $Log: Component.py,v $
# Revision 1.4  2001/08/27 18:29:21  drew_csillag
# * pylibs/AE/Component.py(_realRenderComponent): only tracks
# time if debug flag is set
#
# Revision 1.3  2001/08/09 22:53:40  drew_csillag
# ok, I'm a moron...  Copied the argument list from the def: to the call,
# default arguments included, which of course become keyword arguments....
#
# DUH!!!!!!
#
# Revision 1.2  2001/08/09 22:14:44  drew_csillag
# made so if call fullCallComponent, can figure out if it:
#   a) was rendered
#   b) was expired
#
# Revision 1.1.1.1  2001/08/05 15:00:41  drew_csillag
# take 2 of import
#
#
# Revision 1.19  2001/08/02 22:53:23  drew
# fixed so include actually works
#
# Revision 1.18  2001/07/19 16:00:42  drew
# removed default defer option
#
# Revision 1.17  2001/07/09 20:38:41  drew
# added licence comments
#
# Revision 1.16  2001/07/09 16:32:39  drew
# Component calls now can be yes, no, defer, force, old!
#
# Revision 1.15  2001/04/24 22:48:55  smullyan
# AE.Component.DefaultComponentHandler is now a subclass of
# ComponentHandler(duh).  Beginning to sketch aed_compat service.
#
# Revision 1.14  2001/04/13 04:21:23  smullyan
# removed "file://" protocol for component calls, which made no sense.
#
########################################################################
