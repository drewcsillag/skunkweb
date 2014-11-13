#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#!/usr/local/bin/python
#
# This is a script which facilitates creation of versioned releases
#

import commands
import re
import sys
import os

sys.path.append ( '../pylibs' )
from prompt import *
CVSROOT=open('CVS/Root').read().strip()
# Ask the questions

vers_q = StringQuestion ( 'Please enter the version for this release' )
src_q = StringQuestion ( 'Please enter the directory where source code is checked out in', os.getcwd() )
dist_dir = StringQuestion ( 'Where do you wish the distribution to be created',
                            '/tmp' )
vers_tag = StringQuestion ( 'Please enter the tag for this release' )

print 'Welcome to PyDO distribution creation'
print 'Please answer the following questions'

vers = vers_q.ask()

def_tag = 'PYDO_RELEASE_' + re.sub ( '\.', '_', vers )
vers_tag.setDefault ( def_tag )
tag = vers_tag.ask()

_dir = dist_dir.ask()
src_dir = src_q.ask()

conf_q = BoolQuestion ( 'Are you sure you want to tag current code %s (version %s), and create a distribution in %s' % (tag, vers, _dir), 1 )

if not conf_q.ask():
    sys.exit(0)


#
# Ok, do the work
#
#for d, local in ( ('.', 1), ('AED', 0), ('SDS', 0), ('pylibs', 0), ('misc', 0),
#                  ('schemas', 0) ):
for d, local, single in ( ('pylibs/PyDO', 1, 0), ('pylibs/static.py', 0, 1)):

    # Tag the stuff 
    if local:
       opt = '-l -F '
    else:
       opt = '-F '


    if not single:
        print ( 'Tagging in %s' % (os.path.join ( src_dir, d) ))

        cmd = 'cvs tag %s %s .' % (opt, tag)

        os.chdir ( os.path.join ( src_dir, d ))

        ret, out = commands.getstatusoutput ( cmd )
        if ret:
            print ( 'Tag failed in %s: returned %d: %s' % (d, ret, out))
            sys.exit(1)

    else:
        os.chdir( src_dir )
        file = d
        print 'Tagging %s' % file
        cmd = 'cvs tag %s %s %s' % (opt, tag, file)
        ret, out = commands.getstatusoutput ( cmd )
        if ret:
            print ( 'Tag failed in %s: returned %d: %s' % (d, ret, out))
            sys.exit(1)

#
# Ok, all tagged - create the distribution 
#
os.chdir ( _dir )
d_file = os.path.join ( _dir, 'PyDO-%s.tgz' % vers) 

#doc_cmds=[]
#for i in ['PyDO',]:
#    doc_cmds.append('cd skunkweb-%s/docs/html; make %s/%s.html' % (vers, i, i))
#    doc_cmds.append('cd skunkweb-%s/docs/paper-letter; make %s.ps %s.pdf %s.dvi' % (vers, i,i,i))
#
cmds = (('cvs -d %s export -r %s -d PyDO-%s skunkweb/pylibs/PyDO' % (CVSROOT, tag, vers)),
        ('cvs co -p -r %s skunkweb/pylibs/static.py > PyDO-%s/static.py' % (tag, vers)),
        #+ tuple(doc_cmds) +
        'tar czf %s PyDO-%s' % (d_file, vers),
        'rm -rf PyDO-%s' % vers,
        )
print 'Creating distribution'

for c in cmds:
    print 'command', c
    ret, out = commands.getstatusoutput ( c )
    if ret:
        print ( '"%s" failed: returned %d: %s' % (c, ret, out))
        sys.exit(1)

print 'The new PyDO distribution is now in %s' % d_file 
sys.exit(0)
