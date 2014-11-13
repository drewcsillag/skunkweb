# Time-stamp: <03/01/21 13:49:37 smulloni>

######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>,
#                     Drew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from containers.fieldcontainer import FieldContainer
from form import _getname

class Goto(object):
    def __init__(self, formname, args=None):
        self.formname=formname
        self.args=args
        
    def dispatch(self,
                 form,
                 dispatcher,
                 argdict,
                 ns=None):
        if ns is None:
            ns={}
        form.submit(argdict)
        if form.errors:
            return form
        dispatcher.statemgr.store_form(form)
        form.process(argdict, dispatcher, ns)
        if self.formname:
            return dispatcher.createForm(self.formname, args=self.args)

class Pop(object):
    def __init__(self, args=None):
        self.args=args
        
    def dispatch(self,
                 form,
                 dispatcher,
                 argdict,
                 ns=None):
        if ns is None:
            ns={}
        form.submit(argdict)
        if form.errors:
            return form
        dispatcher.statemgr.store_form(form)        
        form.process(argdict, dispatcher, ns)
        nextformname=dispatcher.statemgr.pop_formname()
        if nextformname:
            f=dispatcher.createForm(nextformname, args=self.args)
            f.setData(dispatcher.statemgr.state.get(nextformname, {}))
            return f

class Push(object):
    def __init__(self, formname, valid=0, args=None):
        self.formname=formname
        self.valid=valid
        self.args=args
        
    def dispatch(self,
                 form,
                 dispatcher, 
                 argdict,
                 ns=None):
        if ns is None:
            ns={}
        if self.valid:
            form.submit(argdict)
            if form.errors:
                return form
        dispatcher.statemgr.store_form(form)                    
        dispatcher.statemgr.push_formname(form.name)
        f=dispatcher.createForm(self.formname, args=self.args)
        f.setData(dispatcher.statemgr.state.get(self.formname, {}))
        return f
    
class AbstractFormDispatcher(object):
    def __init__(self,
                 statemgr,
                 stateVariable='_state'):
        self.statemgr=statemgr
        self.stateVariable=stateVariable

    def createForm(self, formname, argdict=None, args=None):
        raise NotImplementedError

    def getStartForm(self, argdict):
        raise NotImplementedError

    def next(self, form, argdict, ns):
        raise NotImplementedError

    def dispatch(self, argdict, ns):
        # extract the state
        statestr=argdict.get(self.stateVariable)
        if statestr:
            self.statemgr.read(statestr)
        # identify the form being submitted.
        if self.statemgr.stack:
            form=self.createForm(self.statemgr.pop_formname(), argdict)
            # get the next action.
            action=self.next(form,
                             argdict,
                             ns)
            # get the next form, if any
            form=action.dispatch(form,
                                 self,
                                 argdict,
                                 ns)
            
        # if there isn't one, return the start form.
        else:
            form=self.getStartForm(argdict)
            if form:
                form.reset()
        if form:
            # update the state with the new form name
            self.statemgr.push_formname(form.name)
            # set the new state in the form's stateVariable 
            form.fields[self.stateVariable].value=self.statemgr.write()
        return form

class LinearFormDispatcher(AbstractFormDispatcher):
    def __init__(self,
                 statemgr,
                 forms,
                 stateVariable='_state'):
        self.forms=FieldContainer(forms,
                                  fieldmapper=_getname,
                                  storelists=0)        
        AbstractFormDispatcher.__init__(self, statemgr, stateVariable)
        
    def createForm(self, formname, argdict=None):
        return self.forms.get(formname)

    def getStartForm(self, argdict):
        return self.forms[0]

    def next(self, form, argdict, ns):
        ind=self.forms.index(form)+1
        if ind < len(self.forms):
            return Goto(self.forms[ind].name)
        return Goto(None)

__all__=['Goto',
         'Pop',
         'Push',
         'AbstractFormDispatcher',
         'LinearFormDispatcher']
