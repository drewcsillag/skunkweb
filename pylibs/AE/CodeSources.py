#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
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

def updatecache(filename, updcache=linecache.updatecache):
    # XXX Important - do not move to the top of the file, it will
    # get unloaded on restart then!!!
    try:
        import sys
    except: #basically, we're in reload and our namespace is kinda trashed
        return updcache(filename)
        
    #import sys
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
