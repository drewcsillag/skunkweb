######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
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
#
########################################################################
#      Credits: many contributions here from James Richards (especially
#      layout code and composite fields).
########################################################################

from containers import FieldContainer
from form import Field, DomainField, Form, FormErrorMessage, \
     _getname, CompositeField, _defaultValueComposer, \
     FieldProxy
from containers import Set
import ecs

# some base classes.

class Viewable(object):
    def __init__(self, **view_attrs):
        if view_attrs.has_key('value'):
            # setting value as a view attribute is
            # not correct as the value of a field is
            # based initially upon the default value
            raise ValueError, "value is not a settable view attribute"
        self.view_attrs=view_attrs

    def getView(self):
        raise NotImplementedError

class _requirable(object):
    def validate(self, form=None):
        if self.required and self.value in (None, [], ''):
            d={'name' : self.name,
               'description' : self.description}
            try:
                msg=self.required % d
            except TypeError:
                msg="%(description)s is required but has no value" % d
            return [FormErrorMessage(self, msg)]

class ViewableField(_requirable, Field, Viewable):
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 setable=1,
                 **view_attrs):
        self.required = required
        Field.__init__(self, name, description, default, multiple, setable)
        Viewable.__init__(self, **view_attrs)

class ViewableDomainField(_requirable, DomainField, Viewable):
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
                 setable=1,
                 **view_attrs):
        ViewableField.__init__(self,
                               name,
                               description,
                               default,
                               required,
                               multiple=0,
                               setable=setable,
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
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 required=0,
                 setable=1,
                 store_contents=0,
                 **view_attrs):
        self.store_contents=store_contents        
        InputField.__init__(self,
                            name,
                            description,
                            default,
                            required,
                            setable,
                            **view_attrs)

        
    def _set_value(self, val):
        try:
            v=val.filename
        except AttributeError:
            v=val
        InputField._set_value(self, v)
        if self.store_contents:
            try:
                self.contents=val.contents
            except AttributeError:
                self.contents=None

    value=property(InputField._get_value, _set_value)
    
    def clearValue(self):
        if self.store_contents:
            self.contents=None
        InputField.clearValue(self)
        

        

class HiddenField(InputField):
    type="hidden"
    def __init__(self,
                 name,
                 description=None,
                 default=None,
                 setable=0,
                 **view_attrs):
        InputField.__init__(self,
                            name,
                            description,
                            default,
                            setable=setable,
                            **view_attrs)
    
class SubmitField(InputField):
    type="submit"
    def __init__(self,
                 name=None,
                 description=None,
                 default=None,
                 setable=0,
                 **view_attrs):
        InputField.__init__(self,
                            name,
                            description,
                            default,
                            setable=setable,
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
        ViewableField.__init__(self,
                               name,
                               description,
                               default,
                               required,
                               multiple=0,
                               **view_attrs)
        
        
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
    A component view which accepts a list of options for composing a <select>
    field:
    - a list of strings ['1','2', '3'] becomes
      <select>
       <option value="1">1</option>
       <option value="2">2</option>
       <option value="3">3</option>
      </select>

    - a list of two element string tuples
      [('One', '1'), ('Two', '2')] becomes
      <select>
        <option value="1">One</option>
        <option value="2">Two</option>
      </select>

    - a list of tuples, each  containing a string key and a subgroup
      list ['My Subgroup', ['1', '2']]:
      <select>
       <optgroup label="My Subgroup">
        <option value="1">1</option>
        <option value="2">2</option>
       </optgroup>
      </select>

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
                    raise ValueError, \
                          "option group not permitted: %s" % str(oval)
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
                 type=None,
                 **view_attrs):
        self.options, domain=self._parse_options(options, name, multiple, type)
        ViewableDomainField.__init__(self,
                                     name=name,
                                     domain=domain,
                                     description=description,
                                     default=default,
                                     multiple=multiple,
                                     **view_attrs)
        
        
    def _parse_options(self, options, name, multiple, type):
        d=Set()
        optlist=[]
        if isinstance(options, dict):
            options=options.items()
        for o in [self._coerce_option(x, name, multiple, type) for x in options]:
            d.append(o.value)
            optlist.append(o)
        return optlist, d

    def _coerce_option(self, option, name, multiple, type):
        if isinstance(option, ButtonOption):
            return option
        if type==None:
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
        if self.value is None:
            option.checked=None
        elif self.multiple:
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

class SubmitButtonGroupField(ButtonGroupField):
    def __init__(self,
                 name,
                 options,
                 **view_attrs):
        ButtonGroupField.__init__(self,
                                  name,
                                  options,
                                  description=None,
                                  default=None,
                                  multiple=0,
                                  type='submit',
                                  **view_attrs)
    def getView(self):
        table=ecs.Table()
        tr=ecs.Tr()
        for o in self.options:
            tr.addElement(ecs.Td(o.getView()))
        table.addElement(tr)
        table.attributes.update(self.view_attrs)
        return table


class ButtonBar(ViewableDomainField):
    def __init__(self,
                 name,
                 options,
                 **view_attrs):
        self.options, domain=self._parse_options(options)
        ViewableDomainField.__init__(self, name, domain, **view_attrs)

    def _parse_options(self, options):
        d=Set()
        optlist=[]
        for o in options:
            if isinstance(o, tuple):
                d.append(o[0])
                optlist.append(o)
            else:
                d.append(o)
                optlist.append((o, o))
        return optlist, d

    def getView(self):
        tr=ecs.Tr()
        for val, label in self.options:
            b=ecs.Button(label, attributes={'name' : self.name,
                                            'value': val})
            tr.addElement(ecs.Td(b))
        return ecs.Table(tr)
            
            
        

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
        if inputType not in ('radio', 'checkbox', 'submit', 'button'):
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
        if self.inputType in ('radio', 'checkbox') and self.checked:
            elem.setAttribute('checked', 'checked')
        elem.attributes.update(self.view_attrs)
        return elem

########################################################################
# The layouts used to provide form views
########################################################################
class Layout(object):
    "Superclass for ViewableForm layouts"
    def handleError(self, form, tr, fld):
        numErrs = 0
        if form.errors:
            msgs=form.errors.get(fld)
            if msgs:
                msg='\n'.join([x.errormsg for x in msgs])
                numErrs = numErrs + 1
                em=ecs.Em(msg).setAttribute('class', 'form_error')
                pr = ecs.Pre(em)
                td=ecs.Td(pr).setAttribute('colspan', '2')
                tr.addElement(td)
        return numErrs    
    


class FlowLayout(Layout):
    "A simple layout which arranges its items in a columnar, single row view"
    def layoutFields(self, form, table=None):
        """\
        Arranges the given form's ViewableField list into a flow layout,
        disregarding any nesting within the field list...
        all items are arranged in a single row following the order of the field
        list from the first index of the list [and the first index of any
        nested list] to the last index:
        
        [1, [2,3], 4, [5,6,7]]

        produces

        <table>
         <tr>
          <td>1.description</td><td>1.getView()</td>
          <td>2.description</td><td>2.getView()</td>
          <td>3.description</td><td>3.getView()</td>
          <td>4.description</td><td>4.getView()</td>
          <td>5.description</td><td>5.getView()</td>
          <td>6.description</td><td>6.getView()</td>
          <td>7.description</td><td>7.getView()</td>
         </tr>
        </table>
        """
        if table is None:
            table=ecs.Table()
        errTr = ecs.Tr()
        numErr = 0
        for fld in form.fields:
            numErr = numErr + self.handleError(form, errTr, fld)
            
        if numErr:
            table.addElement(errTr)

        tr = ecs.Tr()
        for fld in form.fields:
            if not hasattr(fld, "getView"):
                continue
            
            if fld.description:
                desTd = ecs.Td().addElement(fld.description)
                vwTd = ecs.Td().addElement(fld.getView())
                desTd.setAttribute('valign', 'top')
                vwTd.setAttribute('valign', 'top')
                tr.addElement(desTd)
                tr.addElement(vwTd)
            else:
                td=ecs.Td().addElement(fld.getView())
                td.setAttribute('valign', 'top')
                td.setAttribute('colspan', '2')
                tr.addElement(td)
        tr.addElement('\n')
        table.addElement(tr)
        return table


class StackLayout(Layout):
    "A simple layout which arranges its items in a single column of many rows"
    def layoutFields(self, form, table=None):
        """\
        Arranges the given form's ViewableField list into a stack layout,
        disregarding any nesting within the field list...all items are
        arranged in a single column following the order of the field list
        from the first index of the list [and the first index of any nested
        list] to the last index:
        
        [1, [2,3], 4, [5,6,7]]

        produces

        <table>
         <tr><td>1.description</td><td>1.getView()</td></tr>
         <tr><td>2.description</td><td>2.getView()</td></tr>        
         <tr><td>3.description</td><td>3.getView()</td></tr>
         <tr><td>4.description</td><td>4.getView()</td></tr>
         <tr><td>5.description</td><td>5.getView()</td></tr>
         <tr><td>6.description</td><td>6.getView()</td></tr>
         <tr><td>7.description</td><td>7.getView()</td></tr>
        </table>
        """
        if table is None:
            table=ecs.Table()
        for fld in form.fields:
            if not hasattr(fld, "getView"):
                continue

            errTr = ecs.Tr()
            numErr = self.handleError(form, errTr, fld)
            if numErr:
                table.addElement(errTr)
                
            tr = ecs.Tr()
            if fld.description:
                desTd = ecs.Td().addElement(fld.description)
                vwTd = ecs.Td().addElement(fld.getView())
                desTd.setAttribute('valign', 'top')
                vwTd.setAttribute('valign', 'top')
                tr.addElement(desTd)
                tr.addElement(vwTd)
            else:
                td=ecs.Td().addElement(fld.getView())
                td.setAttribute('valign', 'top')
                td.setAttribute('colspan', '2')
                tr.addElement(td)
            tr.addElement('\n')
            table.addElement(tr)
        return table



class NestedListLayout(Layout):
    "A layout which mimics the structure of a given nested list as a tabular display"
    def layoutFields(self, form, table=None):
        """\
        Arranges the given form's ViewableField list into a tabular display based
        upon the nesting of the given field list...
        column spanning is based upon the maximum depth of the largest nested list:

        [1, [2,3], 4, [5,6,7]]

        produces

        <table>
         <tr>
          <td>1.description</td><td colspan="5">1.getView()</td>
         </tr>
         <tr>
          <td>2.description</td><td>2.getView()</td>
          <td>3.description</td><td colspan="3">3.getView()</td>
         </tr>
         <tr>
          <td>4.description</td><td colspan="5">4.getViews()</td>
         </tr>
         <tr>
          <td>5.description</td><td>5.getView()</td>
          <td>6.description</td><td>6.getView()</td>
          <td>7.description</td><td>7.getView()</td>
         </tr>
        </table>

        where ecs.Table is returned by the method:
        
        1) if a table was passed to the method, the same table is returned with
           the fields laid out inside it
        2) if a table was not passed, the default table is generated and returned
           with the fields laid out 
        """
        if table is None:
            table=ecs.Table()
            
        for tstFnm in form.fieldLayout:
            tr=ecs.Tr() 
            if isinstance(tstFnm, list) or isinstance(tstFnm, tuple):
                self.handleList(form, tstFnm, tr, table)
            else: 
                self.handleField(form, form.fields[tstFnm], tr, table)
            table.addElement(tr)
            table.addElement('\n')
        return table    

    def handleList(self, form, list, tr, table):
        errTr = ecs.Tr()
        ttlErr = 0
        for fnm in list:
            fld = form.fields[fnm]
            # handle the errors display...these will always span two columns
            numErrs = self.handleError(form, errTr, fld)
            if not numErrs:
                # if there were no errors, we need to add an empty TD for
                #this field's error
                errTr.addElement(ecs.Td().setAttribute('colspan', '2')\
                                 .addElement("&nbsp;"))
            else:
                # increment the total number of errors
                ttlErr = ttlErr + numErrs
                                 
        if ttlErr:
            table.addElement(errTr)
        
        # some rows may have less items than the max depth, in which case we should
        # not span the remaining columns or a very ugly GUI is created
        colspan = 0
        lstLen = len(list)
        if lstLen < form.maxDepth:
            # note that there are 2 <td> cells for each item in any row
            colspan = 2 * (form.maxDepth - lstLen)
        
        for idx in range(0, lstLen):
            fnm = list[idx]
            fld = form.fields[fnm]

            if not hasattr(fld, "getView"):
                return
            
            if idx == lstLen - 1:
                # if we are on the last column, add the colspan, else add no
                #colspan
                self.handleField(form, fld, tr, table, colspan, fromList=1)
            else:
                self.handleField(form, fld, tr, table, 0, fromList=1)
                

    def handleField(self, form, f, tr, table, colspan=0, fromList=0):
        if not fromList:
            # if we are not coming from a list [aka handleList()],
            # then this method must check for errors itself
            errTr = ecs.Tr()
            numErr = self.handleError(form, errTr, f)
            if numErr:
                table.addElement(errTr)

        if not hasattr(f, "getView"):
            return 
            
        if f.description:
            desTd = ecs.Td().addElement(f.description)
            vwTd = ecs.Td().addElement(f.getView())
            desTd.setAttribute('valign', 'top')
            vwTd.setAttribute('valign', 'top')
            if colspan:
                vwTd.setAttribute('colspan', colspan)
            tr.addElement(desTd)
            tr.addElement(vwTd)
        else:
            td=ecs.Td().addElement(f.getView())
            td.setAttribute('valign', 'top')
            if colspan:
                td.setAttribute('colspan', colspan)
            else:
                td.setAttribute('colspan', '2')
            tr.addElement(td)
        tr.addElement('\n')
        return 



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
                 processors=None,
                 layout=None,
                 **view_attrs):
        
        Form.__init__(self,
                      name,
                      method,
                      action,
                      enctype,
                      fields,
                      validators,
                      processors)
        Viewable.__init__(self, **view_attrs)
        self.layout=layout or StackLayout()

    def _get_fields(self):
        return self._fields

    def _set_fields(self, fields):
        flatfields, self._fieldLayout, self.maxDepth = self._flattenFields(fields)
        Form._set_fields(self, flatfields)

    fields=property(_get_fields, _set_fields)

    def _get_fieldLayout(self):
        return self._fieldLayout

    def _set_fieldLayout(self, newLayout):
        """\
        Means for manipulating the layout of the fields of a form
        without reinitializing the set of fields.  Expects a possibly
        nested list of field name against which the current layout
        object will construct a view.
        """
        self._fieldLayout=newLayout

    fieldLayout=property(_get_fieldLayout, _set_fieldLayout)     


    def _flattenFields(self, fields):
        """\
        Ensures that the given list of fields is flattened into a
        one-dimensional list as required by Form superclass also
        flattens the fields used for generating a layout into a
        listing of field names which mimics any nesting in the
        original, unflattened field list

        returns

        (flatfields, layoutfields, maxDepth)
        """
        maxDepth = 1 # the longest sublist of fields
        flds = []
        layout = []
        for tstfld in fields:
            if isinstance(tstfld, list) or isinstance(tstfld, tuple):
                sublst = []
                if len(tstfld) > maxDepth:
                    maxDepth = len(tstfld)
                for subfld in tstfld:
                    flds.append(subfld)
                    sublst.append(subfld.name)
                layout.append(sublst)    
            else:         
                flds.append(tstfld)
                layout.append(tstfld.name)
        return (flds, layout, maxDepth)
    

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
        top_level_errors=self.errors.get(self)
        if top_level_errors:
            top_level_error='<br />'.join([x.errormsg for x \
                                           in top_level_errors])
            em=ecs.Em(top_level_error).setAttribute('class',
                                                    'form_error')
            tr=ecs.Tr().addElement(ecs.Td(em)\
                                   .setAttribute('colspan',
                                                 str(2 * self.maxDepth)))
            table.addElement(tr)
            table.addElement('\n')

        self.layout.layoutFields(self, table)    
        elem.addElement('\n')
        elem.addElement(table)
        elem.addElement('\n')
        return elem


########################################################################
# viewable version of the composite field
########################################################################

class ViewableFieldProxy(FieldProxy, Viewable):
    "A viewable version of the FieldProxy which overrides"\
    "the view produced to use the proxied name for "\
    "submissions instead of the name of the proxied field."

    def __init__(self, proxyName, proxiedField):
        FieldProxy.__init__(self, proxyName, proxiedField)

    def getView(self):
        tmpVw = self.field.getView()
        tmpVw.setAttribute('name', self.name)
        return tmpVw

class ViewableCompositeField(Viewable, CompositeField):
    def __init__(self,
                 name,
                 description,
                 default=None,
                 multiple=1,
                 setable=1,
                 componentFields=None,
                 componentFieldDelimiter='_',
                 valueComposer=_defaultValueComposer,
                 layout=None):
        CompositeField.__init__(self,
                                name,
                                description,
                                default,
                                multiple,
                                setable,
                                componentFields,
                                componentFieldDelimiter,
                                valueComposer)

        # must override initialization of composite fields to ensure that ViewableFieldProxies 
        # are used
        tmpComponents = []
        for fld in componentFields:
            prxy = ViewableFieldProxy(self._getComponentName(fld), fld)
            tmpComponents.append(prxy)
        self._fields = FieldContainer(tmpComponents,
                                          fieldmapper=_getname,
                                          storelists=0)

        self.layout=layout or StackLayout()

    def getView(self):
        return self.layout.layoutFields(self)

