# $Id$
# Time-stamp: <01/12/31 12:49:47 smulloni>

######################################################################## 
#  Copyright (C) 2001 Jocob Smullyan <smulloni@smullyan.org>
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
########################################################################

import os.path, re, sys

_adjust_pattern=re.compile('//*$')
_double_slash_pattern=re.compile('//*')
_slash_pattern=re.compile('^/')

def _adjust_user_path(path, prefix='/'):
    "removes slashes at end of path and roots it under prefix"
    s=os.path.join(prefix, _adjust_pattern.sub('', path))
    return _double_slash_pattern.sub('/', s)

def _deslash_path(path):
    "removes slash at beginning"
    return _slash_pattern.sub('', path)

def impliedPaths(paths):
    """
    given a list of paths, returns a list of all implied paths in a unix-style
    filesystem.  Hence, given ["/foo/bar/goo", "/loo/moo/shoe"], returns
    ['/', '/foo', '/foo/bar', '/loo', '/loo/moo']
    """
    implied=[]
    deslashedPaths=map(lambda x: x.endswith('/') and x[:-1] or x, paths)
    for p in deslashedPaths:
        elems=p.split('/')
        for i in range(len(elems)):
            dir=os.path.join('/', '/'.join(elems[:i]))
            if dir not in deslashedPaths and dir not in implied:
                implied.append(dir)
    return implied


def containedPaths(names, dir):
    ## BUG in Python 2.1 (perhaps not 2.1.1, definitely not in 1.5.2):
    ## re.sub(r'\/*$', '\/', dir) adds two slashes, not one.
    ## I would have preferred to shear off all slashes at end
    ## and replace them with one directly in the regex.
    dir='%s/' % re.sub('\/*$', '', dir)
    
    return filter(lambda x, y=dir: x.startswith(y) \
                  and y!=x \
                  and '/' not in x[len(y):-1],
                  names)

def listdir(path, archive_listing):
    adjusted=_adjust_user_path(path)
    return map(lambda x, y=adjusted, r=_slash_pattern: r.sub('', x[len(y):]),
               containedPaths(archive_listing, adjusted))


class Archive:
    """
    does some of the non-archive-format related dirty work
    in managing an archive file
    """

    def __init__(self, prefix='/'):
        self.prefix=prefix
        
    def savePaths(self, namelist):
        self.paths={}
        for name in namelist:
            adjusted=_adjust_user_path(os.path.join(self.prefix, name))
            self.paths[adjusted]=name
        implied=impliedPaths(self.paths.keys())
        for name in implied:
            self.paths[name]=None

    def exists(self, path):
        return self.paths.has_key(_adjust_user_path(path))

    def listdir(self, path):
        return listdir(path, self.archive.paths.keys())

    