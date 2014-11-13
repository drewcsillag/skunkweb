#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import cStringIO

import ErrorHandler

import Component
import Executables
import Logs

def logException():
    out = cStringIO.StringIO()
    ErrorHandler.logError(out)
    
    errorTags = [frame.executable.dt._error_tag
                 for frame in Component.componentStack#[:Component.topOfComponentStack]
                 if isinstance(frame.executable, Executables.STMLExecutable)
                 if hasattr(frame.executable.dt, '_error_tag')]
    if errorTags:
        out.write('Tag traceback (most recent tag last):\n')
        for tag in errorTags:
            if tag:
                out.write('  File "%s", line %s\n' % (tag._name, tag._lineno))
                out.write('    %s\n' % tag.tag)
            else:
                out.write('  File ??, line??\n')

    x = out.getvalue()
    Logs.ERROR(x)
    #return testexc()
    return x

def testexc():
    out = cStringIO.StringIO()
    print >> out, "top of stack is", Component.topOfComponentStack
    for i in zip(range(len(Component.componentStack)), Component.componentStack):
        print >> out, '%d: %s' % i
        if (isinstance(i[1].executable, Executables.STMLExecutable) 
            and hasattr(i[1].executable.dt, '_error_tag')):
            print >> out, 'tag: ', i[1].executable.dt._error_tag
    return out.getvalue()
