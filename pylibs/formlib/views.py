
# HIGHLY PROVISIONAL.

class Field(object):
    def __init__(self,
                 name,
                 default=None,
                 domain=None,
                 value=None,
                 **view_attrs):
        self.name=name
        self.view_attrs=view_attrs
        self.valid=1
        self.domain=domain
        self.default=default
        self.value=value
        
    def getView(self):
        pass

class InputField(Field):
    type=None
        
    def getView(self):
        elem=ecs.Input({'type' : self.type})
        if self.name is not None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.setAttribute('value', set.value)
        elem.attributes.update(self.view_attrs)
        return elem

class DomainFieldGroup(Field):
    def __init__(self,
                 name,
                 domain,
                 default=None,
                 **view_attrs):
        Field.__init__(self, name, domain, default,**view_attrs)
        self.subfields=[self._getWidget(x) for x in self.domain]
        
    def _getWidget(self):
        raise NotImplemented
    
    def getView(self):
        elem=ecs.Span()
        elem.attributes.update(self.view_attrs)
        for v in self.domain:
            elem.addElement(self._getWidgets.getView())
        return elem

class PasswordField(InputField):
    type="password"

class TextFieldField(InputField):
    type="text"

class ButtonInputField(InputField):
    type="button"

class FileField(InputField):
    type="file"

class HiddenField(InputField):
    type="hidden"

class RadioButtonField(InputField):
    type="radio"

class CheckboxField(InputField):
    type="checkbox"

class SubmitField(InputField):
    type="submit"

class ImageField(InputField):
    type="image"

class ButtonField(Field):
    def __init__(self, name, value, content=[], **view_attrs):
        Field.__init__(self, name, value, **view_attrs)
        self.content=content
        
    def getView(self):
        elem=ecs.Button()
        if self.name!=None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.setAttribute('value', self.value)
        for c in self.content:
            elem.addElement(c)
        elem.attributes.update(self.view_attrs)
        return elem
        

class TextAreaField(Field):
        
    def getView(self):
        elem=ecs.Textarea()
        if self.name is not None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.addElement(self.value)
        elem.attributes.update(self.view_attrs)
        return elem

class SelectOption(object):
    def __init__(self,
                 option_text,
                 value=None,
                 selected=None,
                 label=None,
                 **view_attrs):
        self.option_text=option_text
        if value is not None:
            self.value=value
        else:
            self.value=option_text
        self.selected=selected
        self.label=label
        self.view_attrs=view_attrs

    def getView(self):
        elem=ecs.Option()
        elem.addElement(self.option_text)
        if self.selected:
            elem.setAttribute('selected', 'selected')
        if self.label is not None:
            elem.setAttribute('label', self.label)
        elem.attributes.update(self.view_attrs)
        return elem
    
class SelectOptionGroup(object):
    def __init__(self, label, options=None, **view_attrs):
        self.label=label
        self.view_attrs=view_attrs
        if options:
            self.options=options
        else:
            self.options=[]

    def getView(self):
        elem=ecs.OptGroup()
        elem.setAttribute('label', label)
        elem.attributes.update(self.view_attrs)
        for o in self.options:
            elem.addElement(o.getView())
        return elem
    
class SelectField(Field):
    def __init__(self,
                 name=None,
                 multiple=None,
                 options=[],
                 **view_attrs):
        Field.__init__(self, name, **view_attrs)
        self.multiple=multiple
        self.options=[]
        for o in options:
            self.addOption(o)

    def addOption(self, o):
        if isinstance(o, SelectOption) or isinstance(o, SelectOptionGroup):
            o1=o
        else:
            if type(o) == types.DictType:
                o1=SelectOption(**o)
            else:
                o1=SelectOption(*o)
        self.options.append(o1)

    def getView(self):
        elem=ecs.Select()
        if self.name:
            elem.setAttribute('name', self.name)
        if self.multiple:
            elem.setAttribute('multiple', 'multiple')
        elem.attributes.update(self.view_attrs)
        for o in self.options:
            elem.addElement(o.getView())
        return elem
                
            



#class RadioButtonGroupField(FieldGroup): pass
#class CheckBoxGroupField(FieldGroup): pass




