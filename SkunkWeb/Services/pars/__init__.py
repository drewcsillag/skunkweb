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
#$Id: __init__.py,v 1.6 2001/07/30 16:07:29 smulloni Exp $
from SkunkWeb import Configuration, ServiceRegistry, LogObj
import marshal
import errno
import stat

ServiceRegistry.registerService('pars')

PARS=ServiceRegistry.PARS
DEBUG=LogObj.DEBUG
Configuration.mergeDefaults(
    parFiles = [],
    parFallthrough = 1
    )

import templating
import AE.Cache

parDirs = {}
parContents = {}

def _loadParfiles(f):
    print 
    for i in f:
        DEBUG(PARS, 'loading %s' % i)
        f = open(i)
        parDirs[i] = marshal.load(f)
        parContents[i]=f.read()
        
_loadParfiles(Configuration.parFiles)

def _loadMatchers(m):
    for i in m:
        DEBUG(PARS, 'i is %s' % i)
        if i.overlayDict.has_key('parFiles'):
            if not i.overlayDict.has_key('compileCacheRoot') or \
               i.overlayDict['compileCacheRoot'] == \
               Configuration.compileCacheRoot:
                import SkunkExcept
                raise SkunkExcept.SkunkStandardError(
                    'cannot set parFiles (to %s) in a Scope declaration'
                    ' without setting compileCacheRoot or setting it to'
                    ' something different than the global setting (%s)' % (
                    i.overlayDict['parFiles'], Configuration.compileCacheRoot))

            _loadParfiles(i.overlayDict['parFiles'])
        _loadMatchers(i.children())

_loadMatchers(Configuration.matchers)

MAGIC_ALWAYS_FIRST = '@@@//@@@'

def bogusSlash():
    parDirs[MAGIC_ALWAYS_FIRST]= {
        '/': (-1, (040775, 1, 1, 3, 1, 1, 512, 0, 0, 0))}
    parContents[MAGIC_ALWAYS_FIRST] = ''

def fixname(name):
    inslash = 0
    nn = []
    for i in name:
        if i == '/' and not inslash:
            nn.append('/')
            inslash = 1
        elif i != '/':
            if inslash:
                inslash = 0
            nn.append(i)
    return ''.join(nn)
        
def _statDocRoot( name ):
    name = fixname(name)

    DEBUG(PARS, 'doing stat of %s' % name)
    #for i in range(len(parDirs)):
    for i in [MAGIC_ALWAYS_FIRST] + Configuration.parFiles:
        DEBUG(PARS, 'looking in %s' % i)
        if parDirs[i].has_key(name):
            DEBUG(PARS, 'returning %s' % str(parDirs[i][name][1]))
            return parDirs[i][name][1]

    DEBUG(PARS, 'not found')
    if Configuration.parFallthrough:
        DEBUG(PARS, 'falling through')
        return _saveSdr( name )
    
    f = OSError((errno.ENOENT, "No such file or directory"))
    f.strerror = "No such file or directory"
    f.errno = errno.ENOENT
    f.filename = name
    raise f

def _getDocRootModTime( name ):
    return _statDocRoot( name )[stat.ST_MTIME]

def _readDocRoot( name ):
    name = fixname(name)
    DEBUG(PARS, 'doing read of %s' % name)
    #for i in range(len(parDirs)):
    for i in [MAGIC_ALWAYS_FIRST] + Configuration.parFiles:
        if parDirs[i].has_key(name):
            v = parDirs[i][name]
            return parContents[i][v[0]:v[0]+v[1][stat.ST_SIZE]]
    DEBUG(PARS, 'not found')
    if Configuration.parFallthrough:
        DEBUG(PARS, 'falling through')
        return _saveRdr( name )
    f = OSError((errno.ENOENT, "No such file or directory"))
    f.strerror = "No such file or directory"
    f.errno = errno.ENOENT
    f.filename = name
    raise f


_saveRdr = AE.Cache._readDocRoot
_saveGdrmt = AE.Cache._getDocRootModTime 
_saveSdr = AE.Cache._statDocRoot 

AE.Cache._readDocRoot       = _readDocRoot
AE.Cache._getDocRootModTime = _getDocRootModTime
AE.Cache._statDocRoot       = _statDocRoot
bogusSlash()

#DEBUG(PARS, 'files available: %s' % [p.keys() for p in parDirs])
DEBUG(PARS, 'parfiles loaded: %s' % parDirs.keys())
