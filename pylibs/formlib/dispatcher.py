# Time-stamp: <02/12/30 12:32:01 smulloni>
# $Id: dispatcher.py,v 1.11 2002/12/30 17:04:21 smulloni Exp $

######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>,
#                     Drew Csillag <drew_csillag@yahoo.com>
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
########################################################################

from containers.fieldcontainer import FieldContainer
from form import _getname

class Goto:
    def __init__(self, formname):
        self.formname=formname
        
    def dispatch(self,
                 form,
                 state,
                 argdict,
                 formdict,
                 ns=None):
        if ns is None:
            ns={}
        form.submit(argdict)
        if form.errors:
            return form
        state.store_form(form)
        form.process(state, argdict, formdict, ns)
        if self.formname:
            return formdict[self.formname]

class Pop:
    def dispatch(self,
                 form,
                 state,
                 argdict,
                 formdict,
                 ns=None):
        if ns is None:
            ns={}
        form.submit(argdict)
        if form.errors:
            return form
        state.store_form(form)        
        form.process(state, argdict, formdict, ns)
        nextformname=state.pop_formname()
        if nextformname:
            f=formdict[nextformname]
            f.setData(state.state.get(nextformname, {}))
            return f
        

class Push:
    def __init__(self, formname, valid=0):
        self.formname=formname
        self.valid=valid
        
    def dispatch(self,
                 form,
                 state,
                 argdict,
                 formdict,
                 ns=None):
        if ns is None:
            ns={}
        if self.valid:
            form.submit(argdict)
            if form.errors:
                return form
        state.store_form(form)                    
        state.push_formname(form.name)
        f=formdict[self.formname]
        f.setData(state.state.get(self.formname, {}))
        return f
    
class FormDispatcher:
    def __init__(self,
                 statemgr,
                 forms,
                 flowmgr=None,
                 stateVariable='_state'):
        self.forms=FieldContainer(forms,
                                  fieldmapper=_getname,
                                  storelists=0)
        self.statemgr=statemgr
        if flowmgr is None:
            flowmgr=LinearFlowManager(self.forms)
        self.flowmgr=flowmgr
        self.stateVariable=stateVariable

    def dispatch(self, argdict, ns):
        # extract the state
        statestr=argdict.get(self.stateVariable)
        if statestr:
            self.statemgr.read(statestr)
        # identify the form being submitted.
        if self.statemgr.stack:
            form=self.forms[self.statemgr.pop_formname()]
            # get the next action.
            action=self.flowmgr.next(form,
                                     self.statemgr,
                                     argdict,
                                     ns)
            # get the next form, if any
            form=action.dispatch(form,
                                 self.statemgr,
                                 argdict,
                                 self.forms,
                                 ns)
            
        # if there isn't one, return the start form.
        else:
            form=self.flowmgr.getStartForm(argdict)
            if form:
                form.reset()
        if form:
            # update the state with the new form name
            self.statemgr.push_formname(form.name)
            # set the new state in the form's stateVariable 
            form.fields[self.stateVariable].value=self.statemgr.write()
        return form
    
class LinearFlowManager(object):
    def __init__(self, formlist):
        self.formlist=formlist

    def getStartForm(self, argdict):
        return self.formlist[0]

    def next(self, form, state, argdict, ns):
        ind=self.formlist.index(form) + 1
        if ind < len(self.formlist):
            return Goto(self.formlist[ind].name)
        return Goto(None) # end
