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

__all__=['UNDEF', 'Field', 'DomainField', 'Form']

class _undef(object):
    pass
UNDEF=_undef()
del _undef

class Field(object):
    def __init__(self,
                 name,
                 default=None):
        self.name=name
        self._set_default(default)
        self.clearValue()

    def _get_default(self):
        return self.__default

    def _set_default(self, default):
        self.__default=default

    def clearDefault(self):
        self.__default=None

    default=property(_get_default, _set_default)
        
    def _get_value(self):
        if self.__value is not UNDEF:
            return self.__value
        else:
            return self.default

    def _set_value(self, value):
        self.__value=value

    def clearValue(self):
        self.__value=UNDEF

    value=property(_get_value, _set_value)

class DomainField(Field):
    """
    a variety of field in which the
    the possible values of the field consist
    of an enumeration or menu. 
    """
    def __init__(self, name, domain, default=None):
        Field.__init__(self, name, default)
        self._set_domain(domain)
        
    def _get_domain(self):
        return self.__domain

    def _set_domain(self, domain):
        if self.default is not None and self.default not in domain:
            raise ValueError, \
                  "pre-existing default conflicts with new domain; "\
                  "clear the default before setting domain"
        self.__domain=domain

    domain=property(_get_domain, _set_domain)

    def _set_value(self, value):
        if value not in self.domain:
            raise ValueError, "value not present in domain"
        Field._set_value(self, value)
    
    value=property(Field._get_value, _set_value)
    
    def _set_default(self, default):
        if default is not None and default not in self.domain:
            raise ValueError, "default value not present in domain"
        Field._set_default(self, default)

    default=property(Field._get_default, _set_default)        
    

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


##    def validate(self):
##        # should call all validators
##        # and set the valid flags on all
##        # of them -- TBD
##        if 1:
##            pass

##    def _reset(self):
##        # should clean the valid flags.
##        # should it also wipe out the field
##        # values?  Probablee.
##        if 0:
##            print "thing is impossible"

##    def _is_valid(self):
##        if self.validate():
##            return 1
##        return 0

##    valid=property(_is_valid)

