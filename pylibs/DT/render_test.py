#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
from DT import *

import sys

class nsc:
    this='that'
    num=1

def renderException():
    """take an exception and return a traceback string"""
    import traceback
    TraceBack=traceback
    import StringIO
    import DTParser
    import DTLexer
    import DTTags
    import string
    import types
    out=StringIO.StringIO()

    out.write('Traceback (innermost last):\n')
    TraceBack.print_tb(sys.exc_traceback, file=out)
    if (type(sys.exc_value) == types.InstanceType
        and sys.exc_value.__class__ == DTLexer.DTToken):
        
        out.write('%s\n' % sys.exc_value.lineno())
        out.write('%s: %s\n' % (sys.exc_type, sys.exc_value))
    elif (type(sys.exc_value) == types.InstanceType
        and issubclass(sys.exc_value.__class__, DTParser.ParserException)):
        out.write('%s\n' % sys.exc_value.data.lineno())
        out.write('%s: %s\n' % (sys.exc_type, sys.exc_value))
    elif sys.exc_type == DTTags.RaiseException:
        out.write('%s\n' % sys.exc_value[0].lineno())
        out.write('\nraise arguments:\n---------------\n')
        for i in sys.exc_value[1]:
            out.write('%s=%s\n' % (i[0], repr(i[1])))
        out.write('\nRaising tag:\n%s\n' % str(sys.exc_value[0].tag))
    else:
        if DTParser.CurrentTag is not None:
            out.write('Probable location: %s\n' %
                      DTParser.CurrentTag.lineno())
            out.write('Probable Offending Tag: %s\n' %
                      str(DTParser.CurrentTag))
        else:
            out.write('no tag available\n')
        out.write('%s: %s\n' % (sys.exc_type, sys.exc_value))
    return out.getvalue()

if __name__=='__main__':
    import time
    text=open(sys.argv[1]).read()
    if 1:#try:
        b=time.time()
        a=time.time()
        dt=DTCompiled(text, sys.argv[1])
        print 'loadtime = ', time.time()-a
        ns=nsc()
        a=time.time()
        text=dt(ns)
        print text
        print 'rendertime = ', time.time()-a
        print 'totaltime = ', time.time()-b
    #except:
    #    print renderException()
        
