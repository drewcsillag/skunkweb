class StateManager:
    def push(self, formname):
        pass

    def pop(self):
        pass

    def peek(self):
        pass

    def __setitem__(self, key, value):
        pass

    def __getitem__(self, key):
        pass

    def get(self, key, default=None):
        pass

    def load(self, cgiargs):
        pass

    def getView(self):
        pass

    def getState(self):
        pass
        


class FormDispatcher:
    def nextForm():
        """
        returns either a Form object
        or None.
        """
        pass

class Form:
    def getFields():
        """
        returns a list of FormFields
        """
        pass
    
    def isValid():
        """
        returns a boolean
        """
        pass

    def getView():
        """
        returns an object the str() of
        which can be used to print the form,
        or which can be handled in some other
        way.
        """
        pass

class FormField:
    type=None
    def __init__(self):
        self.name=None
        self.value=None
        self.valid=None

    def getView(self):
        pass

class TextFieldFormField(FormField): pass
class PasswordFormField(FormField): pass
class TextAreaFormField(FormField): pass
class RadioButtonGroupFormField(FormField): pass
class CheckBoxGroupFormField(FormField): pass
class SelectFormField(FormField): pass
class ButtonFormField(FormField): pass
class SubmitFormField(FormField): pass
class ImageFormField(FormField): pass
class FileFormField(FormField): pass
class HiddenFormField(FormField): pass

# and other megawidgets, like selects that know what
# to show, date/range choosers, etc.

class Action: pass

class Goto(Action):
    action='GOTO'
    def __init__(self, formname):
        self.formname=formname

class Pop(Action):
    action='POP'
    def __init__(self):
        pass
    
class Push(Action):
    action='PUSH'
    def __init__(self, formname):
        self.formname=formname
    


