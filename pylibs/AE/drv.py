#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sys
sys.path.append('/home/drew/devel/skunk/pylibs')
import Component
Component.globalNamespace['Component'] = Component

import MimeTypes
MimeTypes.loadMimeTypes()

sys.stderr = sys.__stderr__

import Error

try:
    print Component.callComponent('foo.html', {}, cache=1)
except:
    print "an error occurred"
    print Error.logException()

print Component.postRequestRenderList
