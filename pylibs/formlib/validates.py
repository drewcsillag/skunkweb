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

from form import Field, DomainField, Form
from views import *

########################################################################
# Validating fields
########################################################################

class IntegerField(TextField):
    """\
    Restricts validated input to integer values
    """
    def validate(self, form=None):
        supVal = TextField.validate(self)
        if supVal:
            # superclass validation failed
            return supVal

        if self.value:
            try:
                int(self.value)
            except ValueError,ve:
                return {self: str(ve)}
        return None
        

class DoubleField(TextField):
    """\
    Restricts validated input to double values
    """
    def validate(self, form=None):
        supVal = TextField.validate(self)
        if supVal:
            # superclass validation failed
            return supVal

        if self.value:
            try:
                float(self.value)
            except ValueError, ve:
                return {self: str(ve)}
        return None


class DateField(TextField):
    """\
    Restricts validate input to a string which conform to a particular date String
    """
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 formatString='%m/%d/%Y',
                 **view_attrs):
        """\
        Accepts an optional string which represents the date format which the instance will validate against,
        defaults to mm/dd/yyyy format ['%m/%d/%Y']
        """
        TextField.__init__(self, name, description, default, required)
        Viewable.__init__(self, **view_attrs)
        self.format = formatString

    
    def validate(self, form=None):
        supVal = TextField.validate(self)
        if supVal:
            # superclass validation failed
            return supVal

        if self.value:
            try:
                from time import strptime
                strptime(self.value, self.format)
            except ValueError, ve:
                return {self: "%s: Expected format: %s" % (str(ve), self.format)}
        return None
