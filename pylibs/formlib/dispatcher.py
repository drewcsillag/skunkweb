from argextract import extract_args

class Action(object):
    def __init__(self,
                 action=None,
                 *target):
        """action/target can be one of ('GOTO', formname), ('PUSH', formname)
        or ('POP', dontcare)
        """
        self.action = action
        self.target = target 

class FormSet:
    def __init__(self, forms, initformname, statemgr, formFlow = None):
        """
        forms is the list of form objects
        initformname is the first form in the flow
        formFlow is a dict of 'from form name': 'to form name'
        """
        self.forms = {}
        for i in forms:
            self.forms[i.name] = i
        self.statemgr = statemgr
        statemgr.push(initformname)
        self.formFlow = formFlow

    def _split_fields(self, cgiargdict):
        """finds form qualified arguments """
        d = {}
        for k, v in cgiargdict:
            bits = k.split('.')
            if len(bits) == 2 and self.forms.has_key(bits[0]):
                formdict = d.get(bits[0])
                if formdict is None:
                    d[bits[0]] = formdict = {}
                formdict[k] = v
            else:
                otherdict = d.get('_others')
                if otherdict is None:
                    otherdict = d['_others'] = {}
                d['_others'][k] = v
                
    def dispatch(self, cgiargdict, ns):
        """
        call with CONNECTION.args and globals() -- or some other ns dict
        you want accessible from the view method
        """
        self.state.setstate(cgiargdict)
        formname = self.state.peek()
        form = self.forms[formname]
        if form is None:
            raise "InvalidFormName", formname

        formFields = self._split_fields(cgiargdict)
        #otherwise is post from existing form
        form.argMunge(cgiargdict, self.state)
        form.fillDefaults(cgiargdict, self.state)

        #stuff form fields into the state here
        for i in form.fields:
            blank = ()
            item = cgiargdict.get('%s.%s' % (formname, i.name), blank)
            if item is not blank: 
                state[i.name] = item
                
        invalidFields = form.validate(cgiargdict, self.state)

        if invalidFields:
            self.state.invalidFields = invalidFields
            return form.view(self.state, ns)

        # ok, all is fine thus far, which form to go to now?
        if self.formFlow:
            what_to_do = self.formFlow[formname]
            if not isinstance(f, Action):
                what_to_do = what_to_do(cgiargdict, self.state)
        else:
            what_to_do = form.next(cgiargdict, self.state)
            
        if (what_to_do.action == 'POP' or what_to_do.action == 'GOTO'):
            self.state.invalidOtherFields = self.validate(cgiargdict, form)
            if self.state.invalidOtherFields: #validate entire set
                return form.view(self.state, ns)
            
            ret = form.submit(cgiargdict, self.state) #do submit

            if ret: #if true, a submission error occurred
                return form.errorview(cgiargdict, self.state, ret, ns)
            else:
                if what_to_do.action == 'GOTO':
                    nextformname = what_to_do.target
                    
                else:
                    self.state.pop()
                    nextformname = self.state.peek()
                    
                self.state.pop()
                self.state.push(nextformname)
                return self.forms[nextformname].view(self.state, ns)

        elif what_to_do.action == 'PUSH':
            nextformname = what_to_do.target
            self.state.push(nextformname)
            return self.forms[nextformname].view(self.state, ns)

        else:
            raise 'CommandError', ret

    def validate(self, cgiargdict, form):
        pass


class Form:
    def __init__(self, name, fields):
        """as far as the formset is concerned, fields is a sequence of
        things that have a 'name' attribute that is the unqualified field
        name"""
        self.fields = fields
        self.name = name

    def argMunge(self, cgiargdict, state):
        pass

    def fillDefaults(self, cgiargdict, state):
        pass

    def validate(self, cgiargdict, state):
        """
        does whatever validation you want
        returns None if all is ok, otherwise a list of invalid fields
        """
    def submit(self, cgiargdict, state):
        """returning a true value signifies a (likely) persistence error
        as argument validation should be complete before you get here

        if the return value is true, this value will be passed to errorview
        """
        pass

    def view(self, state, ns):
        """show the form"""
        pass

    def next(self, cgiargdict, state):
        """return the next action, if you're not using the formFlow"""
        
    def errorview(self, cgiargdict, state, ret, ns):
        """when submit fails, this is used to handle/display the error to
        the user"""
    
class AutoForm:
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def argMunge(self, cgiargdict, state):
        args = []
        kwargs = {}
        for field in self.fields:
            name = field.name
            argext = field.argsExtractor
            if argext is None:
                args.append(name)
            else:
                kwargs[name] = argext
        d = extractargs(cgiargdict, args, kwargs)
        cgiargdict.update(d)

    def fillDefaults(self, cgiargdict, state):
        pass

    def validate(self, cgiargdict, state):
        pass

    def submit(self, cgiargdict, state):
        pass

    def view(self, state, ns):
        sl =['<form method=POST enctype="multipart/form-data">']
        for i in self.fields:
            sl.append(i.asHTML(state, ns))
        sl.append(state.asHTML())
        sl.append('</form>')
        return '\n'.join(sl)
            
class AutoFormField:
    def __init__(self, fieldName, widget, argsExtractor = None):
        self.name = fieldName
        self.widget = widget
        self.argsExtractor = None

    def asHTML(self, state, ns):
        return self.widget.asHTML(state, ns)


