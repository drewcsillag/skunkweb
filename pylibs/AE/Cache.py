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
#$Id: Cache.py,v 1.2 2001/08/27 18:09:25 drew_csillag Exp $

#### REMINDER; defer time is the stampeding herd preventer that says
#### Gimme a bit of time to render this thing before you go ahead and do it
import time
import marshal
import cPickle
import os
import errno
import socket
import string
import sys
import commands
import stat
import DT
import DT.DTTagRegistry

import cacheKey.cachekey
from Logs import DEBUG, CACHE, ERROR, MEM_COMPILE_CACHE, WEIRD, LOG, DEBUGIT
import MsgCatalog

import cfg

PYCODE_CACHEFILE_VERSION = 1
DT_CACHEFILE_VERSION = 1
CATALOG_CACHEFILE_VERSION = 1
COMPONENT_CACHEFILE_VERSION = 1

#config variables
cfg.Configuration._mergeDefaultsKw(
    documentRoot = '/usr/local/skunk/docroot',
    compileCacheRoot = '/usr/local/skunk/compileCache',
    componentCacheRoot = '/usr/local/skunk/compCache',
    numServers = 0,
    failoverComponentCacheRoot = '/usr/local/skunk/failoverCache',
    maxDeferStale = 3600, # 1 hour
    deferAdvance = 30, # how long to extend the life of a deferred component cache
    failoverRetry = 30, # how long should we use failover before checking NFS again
    useCompileMemoryCache = 0,
    findCommand = '/usr/bin/find',
    sedCommand = '/bin/sed',
    xargsCommand = '/usr/bin/xargs',
    fgrepCommand = '/bin/fgrep'
)
#/config

tagRegistry = DT.DTTagRegistry.get_standard_tags()
compileMemoryCache = {}

_tempCounter = 0
_tempPostfix = 'tmp'
_tempPrefix = "did_not_call_initTempStuff"
_serverFailover = {}

#child init funcs == initTempStuff()

EXPIRED_MODE = 0740
NORMAL_MODE = 0640
##Cached Component Routines
class CachedComponent:
    def __init__( self, exp_time, defer_time, output, full_key ):
        self.full_key = full_key
        self.exp_time = exp_time
        self.out = output 
        self.stale = exp_time >= cfg.Configuration.maxDeferStale + time.time()
        self.ttl = self.exp_time - time.time()
        self.valid = self.ttl >= 0
        if self.valid and defer_time != -1:
            self.valid = defer_time > time.time()

def getCachedComponent( name, argDict, srcModTime = None ):
    #DEBUG(WEIRD, 'argdict is %s' % argDict)
    if srcModTime is None:
        srcModTime = _getDocRootModTime( name )
        
    if cfg.Configuration.componentCacheRoot is None:
        DEBUG(WEIRD, 'no component cache root')
        return None, srcModTime

    path, svr, fullKey = _genCachedComponentPath( name, argDict )
    cachedModTime = _getCCModTime( path, svr )
    if cachedModTime < srcModTime:
        DEBUG(WEIRD, 'source is newer than cached version %d, %d' % (
            cachedModTime, srcModTime))
        return None, srcModTime
    
    dict = _loadCachedComponent( path, svr )
    if not dict:
        DEBUG(WEIRD, '_loadCachedComponent returned None')
        return None, srcModTime
    return CachedComponent(**dict), srcModTime

def putCachedComponent( name, argDict, out, cache_exp_time ):
    if cfg.Configuration.componentCacheRoot is None:
        return
    #DEBUG(WEIRD, 'argdict is %s' % argDict)
    path, svr, fullKey = _genCachedComponentPath( name, argDict )
    _storeCachedComponent( path, {
        'exp_time': cache_exp_time,
        'defer_time': -1,
        'output': out,
        'full_key': fullKey,
        }, svr )
    #write .key file
    _storeCachedComponentKey( path, fullKey, svr )
    
def extendDeferredCachedComponent( name, argDict ):
    if cfg.Configuration.componentCacheRoot is None:
        return
    path, svr, fullKey = _genCachedComponentPath( name, argDict )
    dict = _loadCachedComponent( path, svr )
    if dict:
        dict[ 'defer_time' ]  = time.time() + cfg.Configuration.deferAdvance
        _storeCachedComponent( path, dict, svr )

#stuff to get python code from cache
def _pyCompileFunc( name, data ):
    return compile( '\n'.join(data.split('\r\n')), name, 'exec'), data
def getPythonCode( name, srcModTime ):
    return _getCompiledThing( name, srcModTime, 'pycode', _pyCompileFunc,
                              PYCODE_CACHEFILE_VERSION)

#stuff to get DTs from cache
def _dtCompileFunc( name, data ):
    return DT.compileTemplate( data, name, tagRegistry )
def _dtReconstituteFunc( data ):
    return apply( DT.DT, data )
def _dtUnconstituteFunc( data ):
    return (data.path, data._text, data._compiled, data._meta )
def getDT( name, srcModTime ):
    return _getCompiledThing( name, srcModTime, 'template',
                              _dtCompileFunc, DT_CACHEFILE_VERSION,
                              _dtReconstituteFunc,
                              _dtUnconstituteFunc, )

#stuff to get MsgCats from Cache
def _mcMakeCat( data, name ):
    keyTest = data.keys()[0]
    if type( data[keyTest] ) == type({}):
        return MsgCatalog.MultiLingualCatalog( data, name )
    else:
        return MsgCatalog.MessageCatalog( data, name )

def _mcCompileFunc( name, data ):
    data = eval( data,{'__builtin__': {}} , {} )
    return _mcMakeCat( data, name )

def _mcReconstituteFunc( data ):
    dict, name = data
    return _mcMakeCat( dict, name )

def _mcUnconstituteFunc( data ):
    return data._dict, data._name

def getMessageCatalog( name, srcModTime = None ):
    DEBUG(WEIRD, "getting catalog %s" % name)
    return _getCompiledThing( name, srcModTime, 'message catalog',
                              _mcCompileFunc, CATALOG_CACHEFILE_VERSION,
                              _mcReconstituteFunc,
                              _mcUnconstituteFunc )

#generic way to get and cache compiled things from cache/disk/memory
def _getCompiledThing( name, srcModTime, legend, compileFunc, version,
                       reconstituteFunc = None, unconstituteFunc = None):
    """
    compileFunc      takes the name and the source and returns compiled form
    unconstituteFunc takes the object and produces a marshal-friendly form
    reconstituteFunc takes the unmarshalled form and reconstitutes into
                     the object
    name             is the documentRoot relative path to the thing
    srcModTime       the modification time of the source, if known
    legend           the label to use in debug messages
    version          marhallable thing that if the one in the compile cache
                     doesn't match, we recompile
    """
    #if not caching compiled things, compile it and go
    if cfg.Configuration.compileCacheRoot is None:
        DEBUG(CACHE, "compiling %s" % legend)
        obj = compileFunc( name, _readDocRoot( name ) )
        return obj

    #if using the compile cache, do we have it and if so is it still
    #okay to use (i.e. the mod time check succeeds)
    if cfg.Configuration.useCompileMemoryCache:
        item = compileMemoryCache.get(cfg.Configuration.compileCacheRoot +name)
        if item:
            if srcModTime is None:
                srcModTime = _getDocRootModTime( name )
            if item[0] >= srcModTime:
                DEBUG(MEM_COMPILE_CACHE, "memory %s cache hit" % legend)
                return item[1]

    #try to get a cached form from disk, barring that, return source
    status, ret, srcModTime = _getCompileCache(
        name, srcModTime, version )
    
    #if a cached form was found and version ok, reconstitute, and write to
    #memory cache if appropriate
    if status:
        ret = reconstituteFunc and reconstituteFunc( ret ) or ret
        if cfg.Configuration.useCompileMemoryCache:
            DEBUG(MEM_COMPILE_CACHE, "writing to memory cache (got from disk)")
            compileMemoryCache[cfg.Configuration.compileCacheRoot + name] = (
                srcModTime, ret)
        return ret
    else:
        #we've got source, compile it, write to memory cache if appropriate
        #and write to disk cache
        obj = compileFunc( name, ret )
        if cfg.Configuration.useCompileMemoryCache:
            DEBUG(MEM_COMPILE_CACHE, "writing to memory cache (compiled)")
            compileMemoryCache[cfg.Configuration.compileCacheRoot + name] = (
                srcModTime, obj)
        
        _writeCompileCache( name,
                            (unconstituteFunc and unconstituteFunc(obj) or obj,
                             version),
                            marshal.dumps )
        return obj

#check for a valid cached version (it's newer than the source) and return
#it, if invalid, just return source
def _getCompileCache( name, srcModTime, version ):
    if srcModTime is None:
        srcModTime = _getDocRootModTime( name )
    cacheModTime = _getCompileCacheModTime( name )
    if cacheModTime > srcModTime:
        try:
            ret, vsn = marshal.loads( _readCompileCacheRoot( name ) )
        except ValueError: #marshal got bad shit
            ERROR('marshal.loads got bad stuff from compile cache, ignoring')
            return 0, _readDocRoot( name ), srcModTime 
            
        if vsn == version:
            return 1, ret, srcModTime
        else:
            DEBUG(CACHE, '_gcc() version mismatch, wanted %s, got %s, '
                  'returning source' % (version, vsn))
            return 0, _readDocRoot( name ), srcModTime 
    else:
        return 0, _readDocRoot( name ), srcModTime 

#### basically, some insurance that we don't escape a given root

_normpath = os.path.normpath

def _fixPath( root, path ):
    return '%s/%s' % (root, _normpath(path)) 

### The real disk access routines
#set so we have a tempfile prefix specific to the pid, host, etc.
def initTempStuff():
    global _tempPrefix
    _tempPrefix = '%s_%d' % ( socket.gethostname(), os.getpid() )
    
def _writeDisk( path, data ):
    DEBUG(CACHE, "writing to disk %s" % path)
    try:
        dirname = os.path.split( path ) [ 0 ]
        try:
            os.makedirs( dirname )
        except OSError, val:
            if val.errno != errno.EEXIST:
                raise
        global _tempCounter
        tempfile = "%s/%s.%d.%s" % (
            dirname, _tempPrefix, _tempCounter, _tempPostfix)
        _tempCounter += 1
        open( tempfile, 'wb' ).write( data )
    except IOError, val:
        LOG("ERROR writing tempfile")
        return None
    try:
        os.rename( tempfile, path )
    except OSError, val:
        LOG("ERROR renaming tempfile %s" % str(val))
        return None
    return 1

## compile cache access
def _writeCompileCache( name, thing, serializeFunc):
    DEBUG(CACHE, "writing compile cache")
    path = _fixPath( cfg.Configuration.compileCacheRoot, name + "c" )
    try:
        _writeDisk( path, serializeFunc( thing ) )
    except:
        ERROR("error writing to compile cache: %s" % sys.exc_info[1])

def _getCompileCacheModTime( name ):
    DEBUG(CACHE, "statting compile cache")
    path = _fixPath( cfg.Configuration.compileCacheRoot, name + "c" )
    try:
        return _getLastChangeTime(path) 
    except:
        return -1

def _readCompileCacheRoot( name ):
    DEBUG(CACHE, "reading compile cache")
    path = _fixPath( cfg.Configuration.compileCacheRoot, name + "c")
    return open( path ).read()


## doc root access
def _statDocRoot( name ):
    #DEBUG(CACHE, "statting doc root")
    path = _fixPath( cfg.Configuration.documentRoot, name )
    #DEBUG(WEIRD, "path is: %s" % path)
    return os.stat(path)
    
def _getDocRootModTime( name ):
    #DEBUG(WEIRD, "docroot is: %s == %s" % (cfg.Configuration.documentRoot,
    #                                       name))
    #DEBUG(CACHE, "statting doc root")
    path = _fixPath( cfg.Configuration.documentRoot, name )
    #DEBUG(WEIRD, "path is: %s" % path)
    # ctime always tracks mtime, but not vice versa, e.g.,
    #in the case of a file being moved.
    return _getLastChangeTime(path)

def _readDocRoot( name ):
    DEBUG(CACHE, "reading doc root")
    path = _fixPath( cfg.Configuration.documentRoot, name )
    return open( path ).read()

## component cache access
def _storeCachedComponent( path, value, svr ):
    DEBUG(CACHE, "storing component output")
    try:
        _writeDisk( path, cPickle.dumps(
            (value, COMPONENT_CACHEFILE_VERSION),
            1))
        os.chmod( path, NORMAL_MODE )
    except IOError, val:
        DEBUG(CACHE, "error storing component", val)
        if val != errno.ENOENT:
            _serverFailover[ svr ] = time.time() + cfg.Configuration.failoverRetry

def _storeCachedComponentKey( path, value, svr ):
    DEBUG(CACHE, "storing component key")
    s = []
    for k, v in value.items():
        s.append("%r %r" % (k, v))
    try:
        _writeDisk( path[:-6] + ".key", "\n".join(s)+"\n" )
    except IOError, val:
        DEBUG(CACHE, "error storing component key %s" % val)
        if val != errno.ENOENT:
            _serverFailover[ svr ] = time.time() + cfg.Configuration.failoverRetry

def _loadCachedComponent( path, svr ):
    DEBUG(CACHE, "loading component output")
    try:
        f = open( path, 'rb' )
        item, version = cPickle.load( f )
        if version != COMPONENT_CACHEFILE_VERSION:
            return
        return item
    except IOError, val:
        if val != errno.ENOENT:
            _serverFailover[ svr ] = time.time() + cfg.Configuration.failoverRetry            
    except: #some other oddball error
        return None
    
def _getCCModTime( path, svr ):
    DEBUG(CACHE, "statting cached component")
    try:
        # ctime, not mtime; see comment for getDocRootModTime, above.
        return _getLastChangeTime(path)
    except OSError, val:
        if val.errno != errno.ENOENT:
            _serverFailover[ svr ] = time.time() + cfg.Configuration.failoverRetry
        DEBUG(CACHE, 'got oserror exception %s' % val)

    return -1

def _getLastChangeTime(path):
    stats=os.stat(path)
    # we believe that this will ALWAYS be equal to ctime, but
    # due to some uncertainty about how Unixes other than FreeBSD, Linux and Solaris
    # may handle ctime, perform this test
    return max(stats[stat.ST_CTIME], stats[stat.ST_MTIME])

#given the path and arguments, generate the path to the component's cached
#representation given the number of shared filesystems (if any) and any
#recent failure info
def _genCachedComponentPath( name, argDict ):
    d = argDict.copy()
    name = _fixPath('', name)
    md5, fullkey = cacheKey.cachekey.genCacheKey( d )
    if cfg.Configuration.numServers:
        serverNo = string.atoi(md5[-4:], 16) % cfg.Configuration.numServers

        if _serverFailover.get(serverNo, 0) == 0:
            return "%s/%s/%s/%s/%s/%s.cache" % (
                cfg.Configuration.componentCacheRoot, serverNo, name, md5[:2],
                md5[2:4], md5), serverNo, fullkey

        elif _serverFailover[serverNo] < time.time():
            _serverFailover[serverNo] = 0
            return "%s/%s/%s/%s/%s/%s.cache" % (
                cfg.Configuration.componentCacheRoot, serverNo, name, md5[:2], md5[2:4],
                md5), serverNo, fullkey

        else:
            return "%s/%s/%s/%s/%s/%s.cache" % (
                cfg.Configuration.failoverComponentCacheRoot, serverNo, name, md5[:2], md5[2:4],
                md5), serverNo, fullkey
    else:
        return "%s/%s/%s/%s/%s.cache" % (
            cfg.Configuration.componentCacheRoot, name, md5[:2], md5[2:4], md5), None, fullkey

def _expireCacheFile( path ):
    try:
        dict, vsn = cPickle.load( open( path ) )
        dict ['exp_time'] = -1
        _writeDisk( path, cPickle.dumps( (dict,vsn), 1 ))
        os.chmod( path, EXPIRED_MODE )
    except:
        pass

def _shellEscape(a):
    na = []
    for i in a:
        if i == "'": na.append("'\"'\"'")
        else: na.append(i)
    return ''.join(na)

def _shellQuote(a):
    na = ["'"]
    for i in a:
        if i == "'": na.append("'\"'\"'")
        else: na.append(i)
    return ''.join(na) + "'"

def clearCache( name, arguments, matchExact = None ):
    if matchExact:
        path, svr, fk = _genCachedComponentPath( name, arguments )
        _expireCacheFile( path )
    else:
        name = _normpath( name )
        md5, fullKey = cacheKey.cachekey.genCacheKey( arguments )
        if cfg.Configuration.numServers:
            names = ' '.join([_shellEscape( "%s/%s/%s" % ( cfg.Configuration.componentCacheRoot,
                                                           i, name ) )
                              for i in range(cfg.Configuration.numServers) ])
        else:
            names = "%s/%s" % (cfg.Configuration.componentCacheRoot, _shellEscape( name ))

        greps = []
        for k, v in fullKey.items():
            #print "--> %r %r" % (k, v)
            greps.append( _shellQuote( "%r %r" % (k, v) ) )
                

        cmd = ('%(find)s %(names)s -name "*.cache" | %(sed)s '
               "'s/.cache$/.key/' ") % {
            'find': cfg.Configuration.findCommand,
            'names': names,
            'sed': cfg.Configuration.sedCommand
            }
        cmd += "|" + " | ".join(["%s %s -l %s" % (
            cfg.Configuration.xargsCommand, cfg.Configuration.fgrepCommand, i )
                                 for i in greps])

        LOG('running command %s' % cmd)
        ret, out = commands.getstatusoutput(cmd)
        #LOG('code %s, out %s' % (ret, out))
        if ret:
            ERROR ( 'Command "%s" returned %d, output:\n%s' % (
                cmd, ret, out ))
            return

        out = [out[:-3]+'cache' for i in out.split('\n')
               if len(i.strip()) and i[:6] != 'find: ']

        LOG('Expiring %s' % out)
        for i in out:
            _expireCacheFile( i )

########################################################################
# $Log: Cache.py,v $
# Revision 1.2  2001/08/27 18:09:25  drew_csillag
# performance tweaks
#
# Revision 1.1.1.1  2001/08/05 15:00:43  drew_csillag
# take 2 of import
#
#
# Revision 1.18  2001/07/29 15:46:16  drew
# altered memory caching so that the compileCacheRoot is part of the memory cache key
#
# Revision 1.17  2001/07/09 20:38:41  drew
# added licence comments
#
# Revision 1.16  2001/04/16 17:53:02  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.15  2001/04/10 22:48:33  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#            
