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

oldimport = __import__
def newimp(*args):
    print "import: ", args[0]
    return oldimport(*args)

#__builtins__.__import__ = newimp

import sys

import cfg
import Logs
import Component
import Error

cfg.Configuration._mergeDict({
    'documentRoot': 'htdocs',
    'componentCacheRoot': 'cache',
    'compileCacheRoot': 'cache',
    #'componentCacheRoot': None,
    #'compileCacheRoot': None,
    'debugFile': sys.stdout,
    'debugFlags': Logs.COMPONENT_TTL,
    'accessFile': None,
    'useCompileMemoryCache': 1,
    })

cfg.serverInit()
cfg.childInit()

##   Component.globalNamespace['Component'] = Component
##   try:
##       print Component.callComponent('foo/index.html', {})
##   except:
##   #    print 'EXCEPTION!!!!'
##       print Error.logException()
##   #print Component.componentStack
##   print Component.callComponent('foo/index.html', {})
##   #import Cache
##   #print Cache.compileMemoryCache.keys()
print Component.callComponent('comp.html', {'foo':'1'}, cache=1)
#Component.callComponent('cctest.html', {})
