from form import *
from views import *

# it would be *very* convenient to use properties here
# (a Python 2.2 feature) -- so I'm thinking about not
# maintaining 2.1 compatibility for this.  I certainly
# don't need to maintain it.
##try:
##    object
##except NameError:
##    class object: pass

# problems to consider:

# 1. I haven't added any code yet to deal with
#    the checked property of checkboxes, radiobuttons.

# 2. some field values are settable with user data, and
#    some are not.  The contents of a dropdown, for instance,
#    or the value associated with a particular radiobutton.
#    Must take care that setting the data in a form does
#    not disturb the programmatically determined characteristics
#    of menu-like inputs.  Similarly, reset() should clear
#    all user selections, but leave menu values and default values.
#    The code sketched out below doesn't deal with that distinction.
#    So, the path for refactoring seems to be to include separate out
#    three kinds of value:
#        1. menu values -- never changed by the user
#        2. default values -- ditto
#        3. user values -- the user's playground.

# My strategy is as follows:

# there is some goodness to be extracted from set.py, but
# it is very incomplete and needs to be reworked.  "set" is also
# not a very helpful name for the module.  So I decided to
# start by doing something brain-dead -- first think of what you need
# to do to create a form

    
##class Form(object):
##    def __init__(self,
##                 name=None,
##                 method='POST',
##                 fields=None):
##        self.name=name
##        self.method=method
##        if fields==None:
##            self.fields=[]
##        else:
##            self.fields=fields
        

##    def _get_data(self):
##        # should gather all the data
##        # from the fields and return them
##        # as a dict -- TBD
##        pass

##    def _set_data(self, data):
##        # should set the values of the fields
##        # from data (a dict) -- TBD
##        pass

##    data=property(_get_data, _set_data)
            
##    def validate(self):
##        # should call all validators
##        # and set the valid flags on all
##        # of them -- TBD
##        pass

##    def _reset(self):
##        # should clean the valid flags.
##        # should it also wipe out the field
##        # values?

##    def _is_valid(self):
##        if self.validate():
##            return 1
##        return 0

##    valid=property(_is_valid)




