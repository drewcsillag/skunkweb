# this needs another go-through, to
# unify selects/buttongroups (& then validation).
# Someone might also want to group together
# a buttongroup and a text field with the same
# name (Other: <textfield>), so nothing
# should be done to make that hard to do,
# although we don't need to rush to implement it.

from form import Field

class ViewableField(Field):
    def __init__(self,
                 name,
                 default=None,
                 value=None,
                 **view_attrs):
        Field.__init__(self, name, default, value)
        self.view_attrs=view_attrs
        
class InputField(ViewableField):
    type=None
        
    def getView(self):
        elem=ecs.Input({'type' : self.type})
        if self.name is not None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.setAttribute('value', set.value)
        elem.attributes.update(self.view_attrs)
        return elem

class DomainFieldGroup(ViewableField):
    def __init__(self,
                 name,
                 domain,
                 default=None,
                 value=None,
                 **view_attrs):
        Field.__init__(self, name, default, value, **view_attrs)
        self._subfields=[self._getWidget(x) for x in self.domain]
        
    def _getWidget(self):
        """
        a subclass should specify what widget to create here.
        """
        raise NotImplemented
    
    def getView(self):
        elem=ecs.Span()
        elem.attributes.update(self.view_attrs)
        for v in self.domain:
            elem.addElement(self._subfields.getView())
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

class ButtonField(ViewableField):
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
        

class TextAreaField(ViewableField):
        
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
    
class SelectField(ViewableField):
    def __init__(self,
                 name=None,
                 default=None,
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




