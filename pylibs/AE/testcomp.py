#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
