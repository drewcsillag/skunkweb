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

from containers import FieldContainer

class Field(object):
    def __init__(self,
                 name,
                 default=None,
                 value=None):
        self.name=name
        self.default=default
        self.__value=value
        # storing this here is not thrilling to me;
        # Drew's errorview() avoids this....
        # self.valid=1
        
    def _get_value(self):
        if self.__value is not None:
            return self.__value
        else:
            return self.default

    def _set_value(self, value):
        self.__value=value

    value=property(_get_value, _set_value)

class Form(object):
    def __init__(self,
                 name=None,
                 method='POST',
                 fields=None):
        self.name=name
        self.method=method
        self.fields=FieldContainer(fields or [],
                                   fieldmapper=lambda x: x.name,
                                   storelists=0)

    def getData():
        d={}
        for k, v in self.fields.iteritems():
            d[k]=v.value
        return d

    def setData(self, data):
        for k, v in data.iteritems():
            if self.fields.has_key(k):
                self.fields[k].value=v

    def validate(self):
        # should call all validators
        # and set the valid flags on all
        # of them -- TBD
        pass

    def _reset(self):
        # should clean the valid flags.
        # should it also wipe out the field
        # values?  Probablee.
        pass

    def _is_valid(self):
        if self.validate():
            return 1
        return 0

    valid=property(_is_valid)

