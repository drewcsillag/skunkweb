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
from containers import Set
import ecs

# some base classes.

class Viewable(object):
    def __init__(self, **view_attrs):
        if view_attrs.has_key('value'):
            # setting value as a view attribute is not correct as the value of a field is
            # based initially upon the default value
            raise ValueError
            
        self.view_attrs=view_attrs

    def getView(self):
        raise NotImplementedError


class ViewableField(Field, Viewable):
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 **view_attrs):
        self.required = required
        Field.__init__(self, name, description, default, multiple)
        Viewable.__init__(self, **view_attrs)


    def validate(self, form=None):
        if self.required and not self.value:
            return {self:"%s is required but has no value" % (self.name)}
        

class ViewableDomainField(DomainField, Viewable):
    def __init__(self,
                 name,
                 domain,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 **view_attrs):
        self.required = required
        DomainField.__init__(self,
                             name,
                             domain,
                             description,
                             default,
                             multiple)
        Viewable.__init__(self, **view_attrs)

class InputField(ViewableField):
    type=None

    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 **view_attrs):
        ViewableField.__init__(self,
                               name,
                               description,
                               default,
                               required,
                               multiple=0,
                               **view_attrs)

    def getView(self):
        elem=ecs.Input({'type' : self.type})
        if self.name is not None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.setAttribute('value', self.value)
        elem.attributes.update(self.view_attrs)
        return elem


########################################################################
# concrete classes.
########################################################################
# First, the one-widget fields.
########################################################################

class PasswordField(InputField):
    type="password"

class TextField(InputField):
    type="text"

class ButtonInputField(InputField):
    type="button"

class FileField(InputField):
    type="file"

class HiddenField(InputField):
    type="hidden"

class SubmitField(InputField):
    type="submit"
    def __init__(self,
                 name=None,
                 description=None,
                 default=None,
                 **view_attrs):
        InputField.__init__(self,
                            name,
                            description,
                            default,
                            **view_attrs)

class ImageField(InputField):
    type="image"

class ButtonField(ViewableField):
    def __init__(self,
                 content,
                 name=None,
                 description=None,
                 default=None,
                 multiple=0,
                 **view_attrs):
        ViewableField.__init__(self,
                               name,
                               description,
                               default,
                               multiple,
                               **view_attrs)
        self.content=content
        
    def getView(self):
        elem=ecs.Button()
        if self.name!=None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.setAttribute('value', self.value)
        if isinstance(self.content, list) or isinstance(self.content, tuple):
            for c in self.content:
                elem.addElement(c)
        else:
            elem.addElement(self.content)
        elem.attributes.update(self.view_attrs)
        return elem
        

class TextAreaField(ViewableField):
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 **view_attrs):
        ViewableField.__init__(self, name, description, default, required,  multiple=0,  **view_attrs)
        
        
    def getView(self):
        elem=ecs.Textarea()
        if self.name is not None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.addElement(self.value)
        elem.attributes.update(self.view_attrs)
        return elem

########################################################################
# now the domain fields.
########################################################################

class SelectField(ViewableDomainField):
    """\
    A component view which accepts a list of options for composing a <select> field:
    - a list of strings ['1','2', '3'] becomes
      <select><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>

    - a list of two element string tuples [('One', '1'), ('Two', '2')] becomes
      <select><option value="1">One</option><option value="2">Two</option></select>

    - a list of tuples, each  containing a string key and a subgroup list ['My Subgroup', ['1', '2']]:
      <select><optgroup label="My Subgroup"><option value="1">1</option><option value="2">2</option></optgroup></select>

    Various combinations of the above basic listing schemes are possible 
    """
    def __init__(self,
                 name,
                 options,
                 description=None,
                 default=None,
                 multiple=0,
                 group_levels=1,
                 **view_attrs):
        self.options, domain=self._parse_options(options,
                                                 max(0, group_levels))
        ViewableDomainField.__init__(self,
                                     name=name,
                                     domain=domain,
                                     description=description,
                                     default=default,
                                     multiple=multiple,
                                     **view_attrs)
        
    def _parse_options(self, options, permit_group=1):
        """
         the options could be:
         - a sequence in which the elements are:
           - SelectOptions;
           - SelectOptionGroups;
           - strings (translated into SelectOptions);
           - 2-tuples (string/string pairs -- also translated
                       into SelectOptions);
           - 2-tuples (string/sequence pairs, with the sequence
                       having the same admissible members as the
                       top-level sequence, with the exception
                       that string/sequence pairs are not permitted
                       to be further nested (by default).  These are
                       translated into SelectOptionGroups).
         - a dict which returns from items() something that meets
           the above criteria.

         If you do want to nest option groups, set group_levels to
         some larger number.  sys.maxint should do it.  If you don't want
         to permit any option groups, set group_levels to zero, or, even
         better, don't try to create any. :)

         """
        optlist=[]
        d=Set()
        if isinstance(options, dict):
            options=options.items()
        for o in [self._coerce_option(x, permit_group) for x in options]:
            d.extend(o.getDomain())
            optlist.append(o)
        return optlist, d

    def _coerce_option(self, option, permit_group=1):
        if isinstance(option, SelectOption):
            return option
        elif isinstance(option, SelectOptionGroup):
            if permit_group:
                return option
            else:
                raise ValueError, "option group not permitted: %s" % option
        elif isinstance(option, str):
            return SelectOption(option)
        elif isinstance(option, tuple):
            if len(option)!=2:
                raise ValueError, "could not parse option: %s" % str(option)
            otext, oval=option
            if isinstance(oval, str):
                return SelectOption(otext, oval)
            else:
                # we should have some sort of container
                # involving an option group.
                if not permit_group:
                    raise ValueError, "option group not permitted: %s" % str(oval)
                # decrement permit_group 
                subopts, subdom=self._parse_options(oval, permit_group-1)
                return SelectOptionGroup(otext, subopts)
        else:
            raise ValueError, "option could not be coerced: %s" % str(option)

    def _update_select_state(self, option):
        # this is supposed to make the option
        # selected depending on the value of the field.
        # we have to deal with option groups.
        if isinstance(option, SelectOptionGroup):
            for o in option.options:
                self._update_select_state(o)
        else:
            v=self.value
            if v is not None:
                if self.multiple:
                    option.selected=option.name in v
                else:
                    option.selected=option.name==v
        
    def getView(self):
       elem=ecs.Select()
       if self.name:
           elem.setAttribute('name', self.name)
       if self.multiple:
           elem.setAttribute('multiple', 'multiple')
       elem.attributes.update(self.view_attrs)
       for o in self.options:
           self._update_select_state(o)
           elem.addElement(o.getView())
       return elem        

########################################################################
# helper classes for SelectField
########################################################################
class SelectOption(Viewable):
    def __init__(self,
                 description,
                 name=None,
                 selected=None,
                 label=None,
                 **view_attrs):
        self.description=description
        if name is not None:
            self.name=name
        else:
            self.name=description
        self.selected=selected
        self.label=label
        Viewable.__init__(self, **view_attrs)
        
    def getView(self):
        elem=ecs.Option()
        elem.addElement(self.description)
        if self.selected:
            elem.setAttribute('selected', 'selected')
        if self.label is not None:
            elem.setAttribute('label', self.label)
        elem.setAttribute('value', self.name)
        elem.attributes.update(self.view_attrs)
        return elem

    def getDomain(self):
        return [self.name]

class SelectOptionGroup(Viewable):
    def __init__(self, label, options=None, **view_attrs):
        Viewable.__init__(self, **view_attrs)
        self.label=label
        if options:
            self.options=options
        else:
            self.options=[]

    def getView(self):
        elem=ecs.Optgroup()
        elem.setAttribute('label', self.label)
        elem.attributes.update(self.view_attrs)
        for o in self.options:
            elem.addElement(o.getView())
        return elem

    def getDomain(self):
        d=Set()
        for o in self.options:
            d.extend(o.getDomain())
        return d

########################################################################
# radio button and checkbox groups
########################################################################

class ButtonGroupField(ViewableDomainField):
    def __init__(self,
                 name,
                 options,
                 description=None,
                 default=None,
                 multiple=0,
                 **view_attrs):
        self.options, domain=self._parse_options(options, name, multiple)
        ViewableDomainField.__init__(self,
                                     name=name,
                                     domain=domain,
                                     description=description,
                                     default=default,
                                     multiple=multiple,
                                     **view_attrs)
        
        
    def _parse_options(self, options, name, multiple):
        d=Set()
        optlist=[]
        if isinstance(options, dict):
            options=options.items()
        for o in [self._coerce_option(x, name, multiple) for x in options]:
            d.append(o.value)
            optlist.append(o)
        return optlist, d

    def _coerce_option(self, option, name, multiple):
        if isinstance(option, ButtonOption):
            return option
        type=multiple and 'checkbox' or 'radio'
        if isinstance(option, str):
            return ButtonOption(name=name,
                                value=option,
                                description=option,
                                inputType=type)
        elif isinstance(option, tuple) and len(option)==2:
            return ButtonOption(name=name,
                                value=option[0],
                                description=option[1],
                                inputType=type)
        raise ValueError, "could not parse option: %s" % option

    def _update_checked_state(self, option):
        if self.multiple:
            option.checked=option.value in self.value
        else:
            option.checked=option.value==self.value

    def getView(self):
        # this is a little more speculative than for a select,
        # since it consists of multiple elements. Override this
        # at will; it is meant to be visually adequate but no more.
        table=ecs.Table()
        for o in self.options:
            self._update_checked_state(o)
            tr=ecs.Tr().addElement(ecs.Td(o.description))
            tr.addElement(ecs.Td().addElement(o.getView()))
            table.addElement(tr)
        table.attributes.update(self.view_attrs)
        return table


########################################################################
# helper classes for button groups
########################################################################

class ButtonOption(Viewable):
    def __init__(self,
                 name,                 
                 description,
                 value=None,
                 inputType='radio',
                 checked=None,
                 **view_attrs):
        if inputType not in ('radio', 'checkbox'):
            raise ValueError, "invalid input type: %s" % inputType
        self.inputType=inputType
        self.checked=checked
        self.name=name
        self.description=description
        if value is not None:
            self.value=value
        else:
            self.value=description
        Viewable.__init__(self, **view_attrs)
        
    def getView(self):
        elem=ecs.Input({'type' : self.inputType})
        if self.name is not None:
            elem.setAttribute('name', self.name)
        if self.value is not None:
            elem.setAttribute('value', self.value)
        if self.checked:
            elem.setAttribute('checked', 'checked')
        elem.attributes.update(self.view_attrs)
        return elem

########################################################################
# the form itself.
########################################################################

class ViewableForm(Viewable, Form):
    def __init__(self,
                 name=None,
                 method=None,
                 action=None,
                 enctype=None,
                 fields=None,
                 validators=None,
                 **view_attrs):
        Form.__init__(self, name, method, action, enctype, fields, validators)
        Viewable.__init__(self, **view_attrs)

    def getView(self):
        elem=ecs.Form()
        if self.method:
            elem.setAttribute('method', self.method)
        if self.enctype:
            elem.setAttribute('enctype', self.enctype)
        if self.action:
            elem.setAttribute('action', self.action)
        elem.attributes.update(self.view_attrs)
        table=ecs.Table()
        table.addElement('\n')
        top_level_error=self.errors.get(self)
        if top_level_error:
            em=ecs.Em(top_level_error).setAttribute('class', 'form_error')
            tr=ecs.Tr().addElement(ecs.Td(em).setAttribute('colspan', '2'))
            table.addElement(tr)
            table.addElement('\n')
        for f in self.fields:
            msg=self.errors.get(f)
            if msg:
                em=ecs.Em(msg).setAttribute('class', 'form_error')
                td=ecs.Td(em).setAttribute('colspan', '2')
                table.addElement(ecs.Tr().addElement(td))
            tr=ecs.Tr()
            if f.description:
                tr.addElement(ecs.Td().addElement(f.description))
                tr.addElement(ecs.Td().addElement(f.getView()))
            else:
                td=ecs.Td().addElement(f.getView()).setAttribute('colspan', '2')
                tr.addElement(td)
            table.addElement(tr)
            table.addElement('\n')
        elem.addElement('\n')
        elem.addElement(table)
        elem.addElement('\n')
        return elem


