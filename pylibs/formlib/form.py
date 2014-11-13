######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#                     Drew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from containers import FieldContainer
from hooks import Hook

__all__=['UNDEF', 'Field', 'DomainField', 'Form', 'FormErrorMessage',
         'CompositeField', 'FieldProxy']

class _undef(object):
    def __str__(self):
        return "UNDEF"

    def __repr__(self):
        return "<UNDEF>"
    
UNDEF=_undef()

class Field(object):
    def __init__(self,
                 name,
                 description="",
                 default=None,
                 multiple=0,
                 setable=1):
        self.name=name
        self.description=description
        self.__multiple=multiple
        self.setable=setable
        if default==None:
            self.clearDefault()
        else:
            self._set_default(default)
        self.clearValue()
 
    def _get_default(self):
        return self._default

    def _set_default(self, default):
        self._default=self.checkValue(default)

    def clearDefault(self):
        self._default=None

    default=property(_get_default, _set_default)
        
    def _get_value(self):
        if not isinstance(self.__value, _undef):
            return self.__value
        else:
            return self.default

    def _set_value(self, value):
        self.__value=self.checkValue(value)

    def clearValue(self):
        self.__value=UNDEF

    value=property(_get_value, _set_value)
    
    def _get_multiple(self):
        return self.__multiple

    multiple=property(_get_multiple)

    def checkValue(self, value):
        isseq=isinstance(value, list) or isinstance(value, tuple)
        if self.multiple and not isseq:
            return value is not None and [value] or []
        elif isseq and not self.multiple:
            raise ValueError, "value cannot be a sequence for this field"
        return value
        
    def validate(self, form=None):
        """\
        Override to return a list of FormErrors
        """
        pass

    def _setData(self, data):
        if self.setable:
            self._set_value(data.get(self.name))
        
        
class FieldProxy(object):
    "A proxy for abstracting a proxied name out from a "\
    "field which may be known by another "\
    "name as a means of indirection"
    def __init__(self, proxyName, proxiedField):
        self._name = proxyName
        self.field = proxiedField

    def __getattr__(self, name):
        if name == 'name':
            return self._name
        else:
            return getattr(self.field, name)
        
    def _get_name(self):
        return self._name
    def _set_name(self, newname):
        self._name = newname
    name=property(_get_name, _set_name)     
        
    def _get_value(self):
        return self.field.value
    def _set_value(self, value):
        self.field.value = value
    value=property(_get_value, _set_value)

def _defaultValueComposer(fieldList):
    """\
    Generates a single 'value' by concatentating each field.value into
    a single newline delimited list
    """
    return '\n'.join([str(fld.value) for fld in fieldList])

class CompositeField(Field):

    "Represents a composite group of fields which are logically"\
    "grouped beneath a single name"

    def __init__(self,
                 name,
                 description="",
                 default=None,
                 multiple=1,
                 setable=1,
                 componentFields=None,
                 componentFieldDelimiter='_',
                 valueComposer=_defaultValueComposer):
        Field.__init__(self,
                       name=name,
                       description=description,
                       default=default,
                       multiple=multiple,
                       setable=setable)
        self.delimiter = componentFieldDelimiter
        if componentFields is None:
            componentFields=[]

        tmpComponents = []
        for fld in componentFields:
            prxy = FieldProxy(self._getComponentName(fld), fld)
            tmpComponents.append(prxy)
        self._fields = FieldContainer(tmpComponents,
                                          fieldmapper=_getname,
                                          storelists=0)
        self.errors=FieldContainer(fieldmapper=_getfield,
                                   storelists=1)
        self.composeValue = valueComposer
                
    def _get_fields(self):
        return self._fields
    fields=property(_get_fields)

    def _getComponentName(self, x):
        """
        Method for generating the keys by which fields are indexed
        within the composite field
        """
        return "%s%s%s" % (self.name, self.delimiter, x.name)

    def _get_value(self):
        """
        The value of a composite field is the result of calling the
        valueComposer on the composite field's component fields.
        """
        return self.composeValue(self.fields)
    value=property(_get_value)
    
    def _setData(self, data):
        if self.setable:
            for ky in data.keys():
                if self.fields.has_key(ky):
                    chgfld = self.fields[ky]
                    chgfld.value = data.get(ky)

class DomainField(Field):
    """
    a variety of field in which the
    the possible values of the field consist
    of an enumeration or menu. 
    """
    def __init__(self,
                 name,
                 domain,
                 description="",
                 default=None,
                 multiple=0,
                 setable=1,
                 lenient=0):
        self.__domain=domain
        self.lenient=lenient
        Field.__init__(self, name, description, default, multiple, setable)
        
    def _get_domain(self):
        return self.__domain

    def _set_domain(self, domain):
        if self.default is not None \
               and not self.in_domain(self.default, domain):
            raise ValueError, \
                  "pre-existing default conflicts with new domain; "\
                  "clear the default before setting domain"
        self.__domain=domain

    domain=property(_get_domain, _set_domain)

    def in_domain(self, value, domain=None):
        if self.lenient:
            return 1
        if (self.multiple and value==[]) or \
           ((not self.multiple) and value==None):
            return 1
        if not domain:
            domain=self.domain
        if value in domain:
            return 1
        if self.multiple and \
               (isinstance(value, list) or isinstance(value, tuple)):
            return reduce(lambda x, y: x and y,
                          [i in domain for i in value])
        return 0

    def checkValue(self, value):
        """
        determines whether the value is permissible for the field.
        This is not meant to perform validation of user input,
        but to prevent programmatic errors.
        """
        value=Field.checkValue(self, value)
        if not self.in_domain(value):
            raise ValueError, "value for '%s' not present in domain: %s" % (self, name, value)
        return value

class Form(object):
    def __init__(self,
                 name=None,
                 method='POST',
                 action="",
                 enctype=None,
                 fields=None,
                 validators=None,
                 processors=None):
        self.name=name
        self.method=method
        self.action=action
        self.enctype=enctype
        self._set_fields(fields)
        self.validators=validators or []
        self.processHook=Hook(processors or [])
        self.submitted=None
        self.errors=FieldContainer(fieldmapper=_getfield,
                                   storelists=1)
        self.state=None

    
    def _get_fields(self):
        return self._fields

    def _set_fields(self, fields):
        self._fields=FieldContainer(fields or [],
                                    fieldmapper=_getname,
                                    storelists=0)

    fields=property(_get_fields, _set_fields)


    def getData(self, prune=1):
        d={}
        for k, v in self.fields.iteritems():
            if prune and k.startswith('_') or not v.setable:
                continue
            d[k]=v.value
        return d

    def setData(self, data):
        for f in self.fields:
            f._setData(data)

    def submit(self, data):
        self.reset()
        self.setData(data)
        self.submitted=1
        self.validate()

    def reset(self):
        for f in self.fields:
            f.clearValue()
        self.submitted=0
        self.errors[:]=[]
        self.state=None
        
    def validate(self):
        self.errors[:]=[]
        for l in ([f.validate for f in self.fields], self.validators):
            for func in l:
                e=func(self)
                if e:
                    self.errors.extend(e)

    def process(self,
                *args,
                **kwargs):
        return self.processHook(self, *args, **kwargs)
    
def _getname(x):
    return x.name

class FormErrorMessage(object):
    def __init__(self, field, errormsg):
        self.field=field
        self.errormsg=errormsg

def _getfield(x):
    return x.field

