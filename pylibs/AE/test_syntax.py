#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import os

for i in os.listdir('.'):
    if len(i)>3 and i[-3:] == '.py':
        try:
            print "compiling", i
            compile(open(i).read(), i, 'exec')
        except:
            print "compilation of %s failed" % i
            
