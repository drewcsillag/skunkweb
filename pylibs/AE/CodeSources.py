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
# $Id: CodeSources.py,v 1.7 2001/07/09 20:38:41 drew Exp $
# Time-stamp: <01/04/10 14:19:30 smulloni>
########################################################################

"""
This contains functionality dealing with sources of templates we evaluate, so 
that we can generate a more intelligent traceback information when something
blows up
"""

import linecache

# Let's cache them here
sources = {}



def getSource ( filename ):
    """get source for a filename that was a template - called by TBLineCache"""
    if not sources.has_key(filename):
        return 
    text = sources[filename]
    return text.split ( '\n' )

def putSource ( filename, source ):
    """put source code in an area reachable by getSources"""
    sources[filename] = source

def clearSources (*args):
    "Gets called after each request is done"
    sources.clear()

def updatecache(filename):
    # XXX Important - do not move to the top of the file, it will
    # get unloaded on restart then!!!
    import sys
    import os
    from stat import ST_MTIME, ST_SIZE
    
    if linecache.cache.has_key(filename):
        del linecache.cache[filename]
    if not filename or filename[0] + filename[-1] == '<>':
        return []
    fullname = filename
    try:
        stat = os.stat(fullname)
    except os.error, msg:
        # Is it one of ours?
        ret = getSource ( filename )
        if ret:
            return ret
        
        # Try looking through the module search path
        basename = os.path.split(filename)[1]
    
        for dirname in sys.path:
            fullname = os.path.join(dirname, basename)
            try:
                stat = os.stat(fullname)
                break
            except os.error:
                pass
            # No luck
            ## print '*** Cannot stat', filename, ':', msg
            return []
    try:
        fp = open(fullname, 'r')
        lines = fp.readlines()
        fp.close()
    except IOError, msg:
        ## print '*** Cannot open', fullname, ':', msg
        return []
    size, mtime = stat[ST_SIZE], stat[ST_MTIME]
    linecache.cache[filename] = size, mtime, lines, fullname
    return lines

def installIntoTraceback():
    linecache._updatecache = linecache.updatecache
    linecache.updatecache = updatecache

class _killGuard:
    def __init__(self):
        self.lc=linecache
    def __del__(self):
        self.lc.updatecache = self.lc._updatecache
        
installIntoTraceback()        
_kg = _killGuard()
