#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import pdb
import Cache
import sys

Cache.numServers = 10
print Cache._genCachedComponentPath('foo/bar.comp', {}, {'lang':2})
Cache._serverFailover[4] = sys.maxint

print Cache._genCachedComponentPath('foo/bar.comp', {}, {'lang':2})

print "logging_p", sys.modules.has_key('Logging')
