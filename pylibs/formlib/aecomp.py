######################################################################## 
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>,
#                     Drew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

"""
viewable form and field implementations that delegate the actual
rendering of forms and fields to AE components.
"""

from AE.Component import callComponent, DT_REGULAR, DT_DATA, NO, rectifyRelativePath
from form import Form
from views import ViewableField, ViewableDomainField, ViewableForm, Viewable

class ComponentViewableMixin(object):
    def __init__(self,
                 component,
                 cache=NO):
        self.component=component
        self.cache=cache

    def getView(self):
        return callComponent(self.component,
                             argDict={'model' : self},
                             compType=DT_REGULAR,
                             cache=self.cache)
    
                                      
                            

class ComponentViewableField(ComponentViewableMixin, ViewableField):
    def __init__(self,
                 name,
                 component,
                 cache=NO,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 setable=1,
                 **view_attrs):
        ViewableField.__init__(self,
                               name,
                               description,
                               default,
                               required,
                               multiple,
                               setable,
                               **view_attrs)
        ComponentViewableMixin.__init__(self,
                                        component,
                                        cache)
        
class ComponentViewableDomainField(ComponentViewableMixin, ViewableDomainField):
    def __init__(self,
                 name,
                 domain,
                 component,
                 cache=NO,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 setable=1,
                 lenient=0,
                 **view_attrs):
        ViewableDomainField.__init__(self,
                                     name,
                                     domain,
                                     description,
                                     default,
                                     required,
                                     multiple,
                                     setable,
                                     lenient,
                                     **view_attrs)
        ComponentViewableField.__init__(self,
                                        component,
                                        cache)
        
class ComponentViewableForm(ComponentViewableMixin, Viewable, Form):
    def __init__(self,
                 component,
                 cache=NO,
                 name=None,
                 method=None,
                 action=None,
                 enctype=None,
                 fields=None,
                 validators=None,
                 processors=None,
                 **view_attrs):
        ComponentViewableMixin.__init__(self,
                                        component,
                                        cache)
        Viewable.__init__(self,
                          **view_attrs)
        Form.__init__(self,
                      name,
                      method,
                      action,
                      enctype,
                      fields,
                      validators,
                      processors)


class ComponentValidator:
    def __init__(self, comp_path):
        self.comp_path=rectifyRelativePath(comp_path)
    def __call__(self, form):
        res=callComponent(comp_path,
                          argDict={'form' : form},
                          compType=DT_DATA,
                          cache=NO)
        # should be a list of FormErrorMessage objects
        return res or []
        
__all__=['ComponentViewableField',
         'ComponentViewableDomainField',
         'ComponentViewableForm',
         'ComponentValidator']
