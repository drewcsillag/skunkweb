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

def process_store(form, argdict, state, ns):
    """
    store the form values in the state dictionary
    if the field name does not begin with an underscore.
    The key for a field value in the state dictionary
    is the formname, a period, and then the fieldname,
    guaranteeing uniqueness.
    """
    state.state.update(dict([('%s.%s' % (form.name, k), v) \
                             for k, v in form.getData().items() \
                             if not k.startswith('_')]))

def process_munge(form, argdict, state, ns):
    """
    this should take the form  data populate
    the previous form on the stack with the item
    indicated in the hidden variable "_mungefield"
    into the field called "_mungetarget".
    
    """
    f=state.peek_form()
    assert f
    target=form.fields['_mungetarget'].value
    source=form.fields['_mungeitem'].value
    f.fields[target].value=form.fields[source].value

def process_submit(form, argdict, state, ns):
    """
    """
    pass

stateVar="_state"
flowactionVar="_flowaction"



actionRE=re.compile(r'^(PUSH|POP|GOTO)(?:\.(.*))?$')

class PushyFlowManager(object):
    def __init__(self, forms):
        self.forms=FieldContainer(forms,
                                  fieldmapper=_getname,
                                  storelists=0)
        
    def getStartForm(self):
        return self.forms[0]

    def next(self, form, state, argdict, ns):
##        print "<h2>in next()</h2>"
##        print argdict
##        print form.name
        if form.name=='confirm':
            if argdict['confirm']=='0':
##                print "<h6>returning a goto</h6>"
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
                f=state.peek_form()
##                print [(k, str(v.value), v.default) for k, v in f.fields.to_dict().items()]
                return Pop()
        else:
##            print "<b>in Goto confirm</b>"
            return Goto('confirm')



