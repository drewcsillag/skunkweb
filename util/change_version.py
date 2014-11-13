#! /usr/bin/python
import os
import commands
import re
import sys

def change_version(srcdir, version):
    for d, f, var, real_f in (('.', 'configure.in', 'SW_VERSION', 'configure'),
                              ('SkunkWeb', 'SkunkWeb/configure.in', 'SW_VERSION', 'configure'),):
       full_f = os.path.join(srcdir, f)
       lines = open(full_f).read()
       pat = re.compile('^%s=.*' % var, re.MULTILINE)
       print 'Changing version in %s' % full_f
       new_lines = pat.sub('%s=%s' % (var, version), lines)
       try:
           f = open(full_f, 'w')
           f.write(new_lines)
           f.close()
       except IOError, val:
           print >> sys.stderr, 'Cannot write %s : %s' % (full_f, val)
           sys.exit(1)


       # Run autoconf
       os.chdir(os.path.join(srcdir, d))
       print "running autoconf...",
       ret, out = commands.getstatusoutput('autoconf')
       if ret:
           print 'Autoconf failed: returned %d: %s' % (ret, out)
           sys.exit(1)
       else:
           print "succeeded"

if __name__=='__main__':
    if len(sys.argv)!=2:
        print >> sys.stderr, "usage: %s version" % os.path.basename(sys.argv[0])
        sys.exit(1)
    version=sys.argv[1]
    path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cwd=os.getcwd()
    try:
        os.chdir(path)
        change_version(path, version)
    finally:
        os.chdir(cwd)
    sys.exit(0)
        
        
