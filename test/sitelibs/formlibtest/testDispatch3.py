"""
<p>Here I need to try out a flow manager that
knows how to PUSH and POP as well as GOTO.

To do this, the form itself will include a value
that means PUSH.  How does the form pushed to know
to pop back?  Its regular submit should be taken to be a pop back unless
there is another indicator.

So let the variable be called "_flowaction".  The value could be
PUSH_<formname> or POP or GOTO_<formname>.  The GOTO could also be just
"next" if the flow is known by the flowmanager (or indeed, any of these symbols
could be replaced).
"""

import re
from containers import FieldContainer
from formlib.form import _getname
from formlib import *



stateVar="_state"
flowactionVar="_flowaction"

actionRE=re.compile(r'^(PUSH|POP|GOTO)(?:\.(.*))?$')

class PushyFlowManager(object):
    def __init__(self, forms):
        self.forms=FieldContainer(forms,
                                  fieldmapper=_getname,
                                  storelists=0)
        
    def getStartForm(self, argdict):
        return self.forms[0]

    def next(self, form, state, argdict, ns):
##        print "<h2>in next()</h2>"
##        print argdict
##        print form.name
        if form.name=='confirm':
            if argdict['confirm']=='0':
##                print "<h6>returning a goto</h6>"
                state.clear()
                return Goto(self.forms[0].name)
##            print "<h6>ending it all</h6>"
            return Goto(None)
        actionCode=argdict.get(flowactionVar)
        if actionCode:
            
##            print "actioncode: %s " % actionCode
            match=actionRE.match(actionCode)
            if not match:
                raise "YOU ARE A SCREWBALL"
            a, f=match.groups()
            if a=='PUSH':
                return Push(f)
            elif a=='GOTO':
                return Goto(f)
            else:
##                f=state.peek_formname()
##                print [(k, str(v.value), v.default) for k, v in f.fields.to_dict().items()]
                return Pop()
        else:
##            print "<b>in Goto confirm</b>"
            return Goto('confirm')



