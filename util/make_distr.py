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
#!/usr/local/bin/python
#
# This is a script which facilitates creation of versioned releases
#
#$Id: make_distr.py,v 1.3 2002/02/13 17:38:48 drew_csillag Exp $

import commands
import re
import sys
import os

sys.path.append ( '../pylibs' )
from prompt import *

# Ask the questions

vers_q = StringQuestion ( 'Please enter the version for this release' )
src_q = StringQuestion ( 'Please enter the directory where source code is checked out in', os.getcwd() )
dist_dir = StringQuestion ( 'Where do you wish the distribution to be created',
                            '/tmp' )
vers_tag = StringQuestion ( 'Please enter the tag for this release' )

print 'Welcome to Skunk distribution creation'
print 'Please answer the following questions'

vers = vers_q.ask()

def_tag = 'SKUNK_RELEASE_' + re.sub ( '\.', '_', vers )
vers_tag.setDefault ( def_tag )
tag = vers_tag.ask()

_dir = dist_dir.ask()
src_dir = src_q.ask()

conf_q = BoolQuestion ( 'Are you sure you want to tag current code %s (version %s), and create a distribution in %s' % (tag, vers, _dir), 1 )

if not conf_q.ask():
    sys.exit(0)

#
# Update the version
#
for d, f, var, real_f in ( ('SkunkWeb', 'SkunkWeb/configure.in', 'SW_VERSION', 'configure'), ):
   full_f = os.path.join ( src_dir, f )
   lines = open ( full_f ).read()
   pat = re.compile ( '^%s=.*' % var, re.MULTILINE )

   print ( 'Changing version in %s' % full_f )

   new_lines = pat.sub ( '%s=%s' % (var, vers), lines )

   try:
       f = open ( full_f, 'w' )
       f.write ( new_lines )
       f.close()
   except IOError, val:
       raise 'Cannot write %s : %s' % (full_f, val)

   # Run autoconf
   os.chdir ( os.path.join(src_dir, d) )

   ret, out = commands.getstatusoutput ( 'autoconf' )

   if ret:
       print ( 'Autoconf failed: returned %d: %s' % (ret, out))
       sys.exit(1)

   # Check the file back in
   print ( 'Checking in %s, %s' % (full_f, real_f) )
   _d, _f = os.path.split ( full_f )
   
   os.chdir ( _d )
   cmd = ( "cvs ci -m 'upped version to %s' %s %s" % (vers, _f, real_f) )

   ret, out = commands.getstatusoutput ( cmd )
   if ret:
       print ( 'Checkin failed: returned %d: %s' % (ret, out))
       sys.exit(1)

   # All done


#
# Ok, do the work
#
#for d, local in ( ('.', 1), ('AED', 0), ('SDS', 0), ('pylibs', 0), ('misc', 0),
#                  ('schemas', 0) ):
for d, local in ( ('.', 1), ('SkunkWeb', 0), ('pylibs', 0), ('docs', 0) ):

    # Tag the stuff 
    if local:
       opt = '-l -F '
    else:
       opt = '-F '

    print ( 'Tagging in %s' % (os.path.join ( src_dir, d) ))

    cmd = 'cvs tag %s %s .' % (opt, tag)

    os.chdir ( os.path.join ( src_dir, d ))

    ret, out = commands.getstatusoutput ( cmd )
    if ret:
        print ( 'Tag failed in %s: returned %d: %s' % (d, ret, out))
        sys.exit(1)

#
# Ok, all tagged - create the distribution 
#
os.chdir ( _dir )
d_file = os.path.join ( _dir, 'skunkweb-%s.tgz' % vers) 

doc_cmds=[]
for i in ['stmlrefer', 'PyDO', 'devel', 'opman']:
    doc_cmds.append('cd skunkweb-%s/docs/html; make %s/%s.html' % (vers, i, i))
    doc_cmds.append('cd skunkweb-%s/docs/paper-letter; make %s.ps %s.pdf %s.dvi' % (vers, i,i,i))

cmds = (('cvs export -r %s -d skunkweb-%s skunkweb' % (tag, vers),)
        + tuple(doc_cmds) +
        ('tar czf %s skunkweb-%s' % (d_file, vers),
         'rm -rf skunkweb-%s' % vers )
        )
print 'Creating distribution'

for c in cmds:
    ret, out = commands.getstatusoutput ( c )
    if ret:
        print ( '"%s" failed: returned %d: %s' % (c, ret, out))
        sys.exit(1)

print 'The new skunk distribution is now in %s' % d_file 
sys.exit(0)
