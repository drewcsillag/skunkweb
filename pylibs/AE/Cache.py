#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#$Id: Cache.py,v 1.17 2003/05/07 18:06:37 drew_csillag Exp $

#### REMINDER; defer time is the stampeding herd preventer that says
#### Gimme a bit of time to render this thing before you go ahead and do it
import time
import marshal
import cPickle
import os
import errno
import socket
import sys
import commands
import stat
import DT
import DT.DTTagRegistry

import cacheKey.cachekey
from Logs import DEBUG, CACHE, ERROR, MEM_COMPILE_CACHE, WEIRD, LOG, DEBUGIT
import MsgCatalog

import cfg
import vfs
import Component
from DT import DTCompilerUtil

PYCODE_CACHEFILE_VERSION = 1
DT_CACHEFILE_VERSION = 1
CATALOG_CACHEFILE_VERSION = 1
COMPONENT_CACHEFILE_VERSION = 1

Configuration=cfg.Configuration

#config variables
Configuration.mergeDefaults(
    documentRoot = '/usr/local/skunk/docroot',
    compileCacheRoot = '/usr/local/skunk/compileCache',
    componentCacheRoot = '/usr/local/skunk/compCache',
    documentRootFS=vfs.LocalFS(),
    numServers = 0,
    failoverComponentCacheRoot = '/usr/local/skunk/failoverCache',
    maxDeferStale = 3600, # 1 hour
    deferAdvance = 30, # how long to extend the life of a deferred component cache
    failoverRetry = 30, # how long should we use failover before checking NFS again
    useCompileMemoryCache = 0,
    findCommand = '/usr/bin/find',
    sedCommand = '/bin/sed',
    xargsCommand = '/usr/bin/xargs',
    fgrepCommand = '/bin/fgrep',
    runOutOfCache = 0,
    dontCacheSource = 0,
    noTagDebug = 0,    
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
        self.stale = exp_time <= Configuration.maxDeferStale + time.time()
        self.ttl = self.exp_time - time.time()
        self.valid = self.ttl >= 0
        if self.valid and defer_time != -1:
            self.valid = defer_time > time.time()

def getCachedComponent( name, argDict, srcModTime = None ):
    #DEBUG(WEIRD, 'argdict is %s' % argDict)
    if srcModTime is None:
        srcModTime = _getDocRootModTime( name )
        
    if Configuration.componentCacheRoot is None:
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
    if Configuration.componentCacheRoot is None:
        return
    path, svr, fullKey = _genCachedComponentPath( name, argDict )
    _storeCachedComponent( path, {
        'exp_time': cache_exp_time,
        'defer_time': -1,
        'output': out,
        'full_key': fullKey,
        }, svr )
    # write .key file
    _storeCachedComponentKey( path, fullKey, svr )
    
def extendDeferredCachedComponent( name, argDict ):
    if Configuration.componentCacheRoot is None:
        return
    path, svr, fullKey = _genCachedComponentPath( name, argDict )
    dict = _loadCachedComponent( path, svr )
    if dict:
        dict[ 'defer_time' ]  = time.time() + Configuration.deferAdvance
        _storeCachedComponent( path, dict, svr )

#stuff to get python code from cache
def _pyCompileFunc( name, data ):
    if Configuration.dontCacheSource:
            return compile( '\n'.join(data.split('\r\n')), name, 'exec'), ''
    else:
        return compile( '\n'.join(data.split('\r\n')), name, 'exec'), data

def getPythonCode( name, srcModTime ):
    return _getCompiledThing( name, srcModTime, 'pycode', _pyCompileFunc,
                              PYCODE_CACHEFILE_VERSION)

#stuff to get DTs from cache
def dt_no_tag_debug(indent, codeout, tag):
    """put some code to mark where we are in terms of execution"""
    codeout.write(indent, '__d.CURRENT_TAG = ""')
    codeout.write(indent, '__d.CURRENT_LINENO = %s' % repr(tag.filelineno()))

def _dtCompileFunc( name, data ):
    if Configuration.noTagDebug:
        otagdbg = DTCompilerUtil.tagDebug
        DTCompilerUtil.tagDebug = dt_no_tag_debug
        obj = DT.compileTemplate( data, name, tagRegistry )
        DTCompilerUtil.tagDebug = otagdbg
        return obj
    else:
        return DT.compileTemplate( data, name, tagRegistry )

def _dtReconstituteFunc( data ):
    return apply( DT.DT, data )

def _dtUnconstituteFunc( data ):
    if Configuration.dontCacheSource:
        return (data.path, '', data._compiled, data._meta )
    else:
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
    return _getCompiledThing(Component._rectifyRelativeName(name),
                             srcModTime,
                             'message catalog',
                             _mcCompileFunc,
                             CATALOG_CACHEFILE_VERSION,
                             _mcReconstituteFunc,
                             _mcUnconstituteFunc)

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
    if Configuration.compileCacheRoot is None:
        DEBUG(CACHE, "compiling %s" % legend)
        obj = compileFunc( name, _readDocRoot( name ) )
        return obj

    #if using the compile cache, do we have it and if so is it still
    #okay to use (i.e. the mod time check succeeds)
    if Configuration.useCompileMemoryCache:
        item = compileMemoryCache.get(Configuration.compileCacheRoot +name)
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
        if Configuration.useCompileMemoryCache:
            DEBUG(MEM_COMPILE_CACHE, "writing to memory cache (got from disk)")
            compileMemoryCache[Configuration.compileCacheRoot + name] = (
                srcModTime, ret)
        return ret
    else:
        #we've got source, compile it, write to memory cache if appropriate
        #and write to disk cache
        obj = compileFunc( name, ret )
        if Configuration.useCompileMemoryCache:
            DEBUG(MEM_COMPILE_CACHE, "writing to memory cache (compiled)")
            compileMemoryCache[Configuration.compileCacheRoot + name] = (
                srcModTime, obj)
        if not Configuration.runOutOfCache:
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
    if cacheModTime > srcModTime or Configuration.runOutOfCache:
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

#_normpath = os.path.normpath
import skunklib._normpath
_normpath = skunklib.normpath

def _fixPath( root, path ):
    return _normpath('%s/%s' % (root,path)) 

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
    path = _fixPath( Configuration.compileCacheRoot, name + "c" )
    try:
        _writeDisk( path, serializeFunc( thing ) )
    except:
        ERROR("error writing to compile cache: %s" % sys.exc_info()[1])

def _getCompileCacheModTime( name ):
    DEBUG(CACHE, "statting compile cache")
    path = _fixPath( Configuration.compileCacheRoot, name + "c" )
    try:
        return os.stat(path)[stat.ST_CTIME] 
    except:
        return -1

def _readCompileCacheRoot( name ):
    DEBUG(CACHE, "reading compile cache")
    path = _fixPath( Configuration.compileCacheRoot, name + "c")
    return open( path ).read()

def _getPathAndMinistat(name):
    path=_fixPath(Configuration.documentRoot, name)
    st=Configuration.documentRootFS.ministat(path)
    return (path, st)

def _getPathFSAndMinistat(name):
    """
    deprecated; use _getPathAndMinistat() instead
    """
    path, st=_getPathAndMinistat(name)
    return path, Configuration.documentRootFS, st

## doc root access
def _statDocRoot(name):
    path, fs, st=_getPathFSAndMinistat(name)
    return st
    
def _getDocRootModTime(name):
    path, fs, st=_getPathFSAndMinistat(name)
    return st[vfs.MST_CTIME]
        
def _readDocRoot(name):
    DEBUG(CACHE, "reading doc root")
    path, fs, st=_getPathFSAndMinistat(name)
    return fs.open(path).read()

def _openDocRoot(name, mode='r'):
    """
    returns an open file object
    """
    path, fs, st=_getPathFSAndMinistat(name)
    return fs.open(path, mode)

def _findPath(name, root='/'):
    docroot=Configuration.documentRoot
    path=_fixPath(docroot, name)
    root=_fixPath(docroot, root)
    dname, fname=os.path.split(path)
    ret=Configuration.documentRootFS.find_path(dname, fname, root)
    if not ret:
        raise FileNotFoundException, path
    ret=ret[len(docroot):]
    if not ret.startswith('/'):
        return '/%s' % ret
    return ret

## component cache access
def _storeCachedComponent( path, value, svr ):
    DEBUG(CACHE, "storing component output")
    try:
        _writeDisk(path,
                   cPickle.dumps((value,
                                  COMPONENT_CACHEFILE_VERSION),
                                 1))
        os.chmod( path, NORMAL_MODE )
    except IOError, val:
        DEBUG(CACHE, "error storing component %s" % val)
        if val != errno.ENOENT:
            _serverFailover[ svr ] = time.time() + Configuration.failoverRetry

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
            _serverFailover[ svr ] = time.time() + Configuration.failoverRetry

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
            _serverFailover[ svr ] = time.time() + Configuration.failoverRetry            
    except: #some other oddball error
        return None
    
def _getCCModTime( path, svr ):
    DEBUG(CACHE, "statting cached component")
    try:
        return os.stat(path)[stat.ST_CTIME]
    except OSError, val:
        if val.errno != errno.ENOENT:
            _serverFailover[ svr ] = time.time() + Configuration.failoverRetry
        DEBUG(CACHE, 'got oserror exception %s' % val)

    return -1

#given the path and arguments, generate the path to the component's cached
#representation given the number of shared filesystems (if any) and any
#recent failure info
def _genCachedComponentPath( name, argDict ):
    d = argDict.copy()
    name = _fixPath('', name)
    md5, fullkey = cacheKey.cachekey.genCacheKey( d )
    if Configuration.numServers:
        serverNo = int(md5[-4:], 16) % Configuration.numServers

        if _serverFailover.get(serverNo, 0) == 0:
            return "%s/%s/%s/%s/%s/%s.cache" % (
                Configuration.componentCacheRoot, serverNo, name, md5[:2],
                md5[2:4], md5), serverNo, fullkey

        elif _serverFailover[serverNo] < time.time():
            _serverFailover[serverNo] = 0
            return "%s/%s/%s/%s/%s/%s.cache" % (
                Configuration.componentCacheRoot, serverNo, name, md5[:2], md5[2:4],
                md5), serverNo, fullkey

        else:
            return "%s/%s/%s/%s/%s/%s.cache" % (
                Configuration.failoverComponentCacheRoot, serverNo, name, md5[:2], md5[2:4],
                md5), serverNo, fullkey
    else:
        return "%s/%s/%s/%s/%s.cache" % (
            Configuration.componentCacheRoot, name, md5[:2], md5[2:4], md5), None, fullkey

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
        if Configuration.numServers:
            names = ' '.join([_shellEscape( "%s/%s/%s" % ( Configuration.componentCacheRoot,
                                                           i, name ) )
                              for i in range(Configuration.numServers) ])
        else:
            names = "%s/%s" % (Configuration.componentCacheRoot, _shellEscape( name ))

        greps = []
        for k, v in fullKey.items():
            #print "--> %r %r" % (k, v)
            greps.append( _shellQuote( "%r %r" % (k, v) ) )
                

        cmd = ('%(find)s %(names)s -name "*.cache" | %(sed)s '
               "'s/.cache$/.key/' ") % {
            'find': Configuration.findCommand,
            'names': names,
            'sed': Configuration.sedCommand
            }
        cmd += "|" + " | ".join(["%s %s -l %s" % (
            Configuration.xargsCommand, Configuration.fgrepCommand, i )
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
# Revision 1.17  2003/05/07 18:06:37  drew_csillag
# added noTagDebug
#
# Revision 1.16  2003/05/01 20:45:58  drew_csillag
# Changed license text
#
# Revision 1.15  2003/04/19 14:19:35  smulloni
# changes for scopeable
#
# Revision 1.14  2003/04/03 15:12:50  drew_csillag
# dded runOutOfCache and dontCacheSource
# 	options
#
# Revision 1.13  2003/01/13 17:56:22  smulloni
# fixed typo in writeCompileCache.
#
# Revision 1.12  2002/11/08 21:18:07  smulloni
# damn, left out an import.
#
# Revision 1.11  2002/11/08 21:16:20  smulloni
# Fix for relative paths for specifying message catalogs; added Input to
# ecs (had been left out due to typo).
#
# Revision 1.10  2002/06/18 15:08:19  drew_csillag
# fixed a DEBUG msg pointed out by pychecker and changed a string.atoi to int()
#
# Revision 1.9  2002/04/09 21:27:34  smulloni
# fix from Stephen Coursen for cache bug
#
# Revision 1.8  2002/02/13 18:36:19  drew_csillag
# fixed typo error
#
# Revision 1.7  2002/02/07 07:18:41  smulloni
# documentRootFS is now a single instance.
#
# Revision 1.6  2002/01/27 03:10:44  smulloni
# moving in the direction of getting rid of Configuration.DocumentRoot!
#
# Revision 1.5  2001/12/02 20:57:50  smulloni
# First fold of work done in September (!) on dev3_2 branch into trunk:
# vfs and PyDO enhancements (webdav still to come).  Also, small enhancement
# to templating's <:img:> tag.
#
# Revision 1.4.2.1  2001/09/19 05:07:15  smulloni
# first code using vfs
#
# Revision 1.4  2001/08/28 11:38:07  drew_csillag
# now uses skunklib.normpath
#
# Revision 1.3  2001/08/27 19:52:51  drew_csillag
# commented out more DEBUG statements
#
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
