######################################################################## 
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>,
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

"""
viewable form and field implementations that delegate the actual
rendering of forms and fields to AE components.
"""

from AE.Component import callComponent, DT_REGULAR, NO

from views import ViewableField, ViewableDomainField, ViewableForm

class ComponentViewableMixin(object):
    def __init__(self,
                 component,
                 cache=NO)
                 **view_attrs):
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
                 cache=YES,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 setable=1,
                 **view_attrs):
        super(ViewableField, self).__init__(self,
                                            name,
                                            description,
                                            default,
                                            required,
                                            multiple,
                                            setable,
                                            **view_attrs)
        super(ComponentViewableField, self).__init__(self,
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
        super(ViewableDomainField, self).__init__(self,
                                                  name,
                                                  domain,
                                                  description,
                                                  default,
                                                  required,
                                                  multiple,
                                                  setable,
                                                  lenient,
                                                  **view_attrs)
        super(ComponentViewableField, self).__init__(self,
                                                     component,
                                                     cache)
