######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
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

from form import FormError
from views import TextField
import time

__all__=['IntegerField', 'DoubleField', 'DateField']

########################################################################
# Validating fields
########################################################################

class IntegerField(TextField):
    "Restricts validated input to integer values"
    def validate(self, form=None):
        errorlist= TextField.validate(self) or []
        if self.value:
            try:
                int(self.value)
            except ValueError, ve:
                errorlist.append(FormError(self, str(ve)))
        return errorlist
        

class DoubleField(TextField):
    "Restricts validated input to double values"
    
    def validate(self, form=None):
        errorlist=TextField.validate(self) or []
        if self.value:
            try:
                float(self.value)
            except ValueError, ve:
                errorlist.append(FormError(self, str(ve)))
        return errorlist


class DateField(TextField):
    "Restricts validated input to a string which parseable according to"\
    "a specified format."
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 formatString='%m/%d/%Y',
                 **view_attrs):
        """\
        Accepts an optional string which represents the date format
        which the instance will validate against,
        defaults to mm/dd/yyyy format ['%m/%d/%Y']
        """
        TextField.__init__(self,
                           name,
                           description,
                           default,
                           required,
                           **view_attrs)
        self.format = formatString

    
    def validate(self, form=None):
        errorlist=TextField.validate(self) or []

        if self.value:
            try:
                time.strptime(self.value, self.format)
            except ValueError, ve:
                msg="%s: Expected format: %s" % (str(ve), self.format)
                errorlist.append(FormError(self, msg))
        return errorlist
