#! /usr/bin/env python
# Copyright 2001, Zolera Systems, Inc.  See below.
# $Header: /home/users/smulloni/skunkweb/skunkweb/pylibs/wizard.py,v 1.1 2002/02/22 20:56:07 smulloni Exp $
# Uses Python 2.0.

import Tkinter as Tk
import tkFont, tkMessageBox, tkFileDialog
import socket

## When to validate
persheet= 1
atend   = 2

## How to align pages
align_l = 1
align_c = 2
align_r = 3

class _Base:
    'Base class for all sheets and fields.'
    def __init__(self, **kw):
        self.kw = kw.copy()
        self.validate = None
        self.longvalidate = self.kw.get('longvalidate', 0)

class _SheetBase(_Base):
    'Base class for all sheets.'
    def __init__(self, title, textsheet, **kw):
	_Base.__init__(self, **kw)
        self.title = title
	self.next_text = self.kw.get('next')
	self.back_text = self.kw.get('back')
	if textsheet:
	    self.ftdict = self.kw.get('font')
	    self.height = self.kw.get('height', 10)
	    self.width = self.kw.get('width', 40)
	    self.wrap = self.kw.get('wrap', Tk.WORD)
	    self.hscrollbar = self.kw.get('hscrollbar', 0)

class LicenseSheet(_SheetBase):
    'A sheet with text that the user is expected to read.'
    def __init__(self, title, text, **kw):
        _SheetBase.__init__(self, title, 1, **kw)
        self.text = text or ''
        self.mustread = self.kw.get('mustread', 0)
        self.file = self.kw.get('file')

class DynamicSheet(_SheetBase):
    'A sheet generated at display time.'
    def __init__(self, title, builder, **kw):
        _SheetBase.__init__(self, title, 1, **kw)
        self.builder = builder

class Sheet(_SheetBase):
    'A sheet with fields to be filled in.'
    def __init__(self, title, fields, **kw):
        _SheetBase.__init__(self, title, 0, **kw)
        self.fields = fields

class SpacerField(_Base):
    'A spacer; leave a blank line.'
    def __init__(self, **kw):
        _Base.__init__(self, **kw)
        self.lines = self.kw.get('lines', 1)

class LabelField(_Base):
    'A label -- text only.'
    def __init__(self, prompt, **kw):
        _Base.__init__(self, **kw)
        self.prompt = prompt
        self.ftdict = self.kw.get('font')
        alignment = self.kw.get('align', align_l)
        if alignment == align_l:
            self.sticky = Tk.W
        elif alignment == align_r:
            self.sticky = Tk.E
        else:
            self.sticky = Tk.E + Tk.W

class EntryField(_Base):
    'Basic text entry field.'
    def __init__(self, key, prompt, **kw):
        _Base.__init__(self, **kw)
        self.key, self.prompt = key, prompt
        self.private = self.kw.get('private', 0)
        self.validate = self.kw.get('validate')
        self.startdisabled = self.kw.get('startdisabled', 0)
        self.entrywidth = self.kw.get('entrywidth', 0)

class FileField(EntryField):
    'A filename entry field.'

class DirField(EntryField):
    'A Directory entry field.'

# Get Tkinter's askdirectory; create our own if not using Python2.2
try:
    askdirectory = tkFileDialog.askdirectory
except:
    from tkFileDialog import _Dialog
    class Directory(_Dialog):
	command = "tk_chooseDirectory"
    def askdirectory(**options):
	return Directory(**options).show()

_isentry = lambda f: isinstance(f, EntryField) \
	or isinstance(f, FileField) or isinstance(f, DirField)

class CBField(_Base):
    'A checkbox.'
    def __init__(self, key, prompt, **kw):
        _Base.__init__(self, **kw)
        self.key, self.prompt = key, prompt
        self.slave = self.kw.get('enables')

class RBField(_Base):
    'Radio buttons for a set of choices.'
    def __init__(self, key, choices, **kw):
        _Base.__init__(self, **kw)
        self.key, self.choices = key, choices[:]

class DDField(_Base):
    'Like RBfield, but the choices show in a drop-down list.'
    def __init__(self, key, prompt, choices, **kw):
        _Base.__init__(self, **kw)
        self.key, self.prompt, self.choices = key, prompt, list(choices[:])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class InvalidEntry(Exception):
    'Exception to be thrown when an entry is invalid.'
    def __init__(self, text=None):
        self.text = text

class Validator:
    'Base class for validation functions.'
    def validate(self, dict, field):
        'This method should raise an InvalidEntry exception on errors.'
        pass

class PassConfirm(Validator):
    'A class to validate that a password and its confirmation match.'
    def __init__(self, what, confirm):
        'Constructor; give the account type and the confirming field name.'
        self.what, self.confirm = what, confirm
    def validate(self, dict, field):
        if len(dict[field]) == 0:
            raise InvalidEntry('Must provide %s password.' % self.what)
        if dict[field] != dict[self.confirm]:
            raise InvalidEntry('Mismatched %s passwords.' % self.what)

class Nonblank(Validator):
    'A class to validate that a field has text in it.'
    def __init__(self, what):
        self.what = what
    def validate(self, dict, field):
        if len(dict[field]) == 0:
            raise InvalidEntry('Must specify %s.' % self.what)

class PositiveNumber(Validator):
    'A class to verify that a number greater than zero was entered.'
    def __init__(self, what):
        self.what = what
    def validate(self, dict, field):
        i = -1
        try:
            i = int(dict[field])
        except:
            i = -1
        if i <= 0:
            raise InvalidEntry('%s must be greater than zero.' % self.what)

class InactivePort(PositiveNumber):
    'A class to verify that a port number is not in use.'
    def __init__(self, what):
        self.what = what
    def validate(self, dict, field):
        PositiveNumber.validate(self, dict, field)
        i = int(dict[field])
        if i > 65535:
            raise InvalidEntry('%s port number too big' % self.what)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', i))
            s.close()
        except:
            return
        raise InvalidEntry('%s port (%d) already in use.' % (self.what, i))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class _DataField:
    'A field that the user enters data into.'
    def __init__(self, wizard, field, sheetnum, widget):
        self.wizard, self.field, self.key, self.sheetnum, self.widget = \
	    wizard, field, field.key, sheetnum, widget
    def get(self):
        return self.widget.get()
    def set(self, text):
        self.widget.delete(0, Tk.END)
        self.widget.insert(Tk.INSERT, text)
    def help(self, event=None):
        self.wizard.helpobj.help(self.wizard, self.key)

class _ButtonField(_DataField):
    'A field with button(s).'
    def __init__(self, wizard, field, sheetnum, widget, tclvar):
        _DataField.__init__(self, wizard, field, sheetnum, widget)
        self.tclvar = tclvar
    def get(self):
        return str(self.tclvar.get())
    def set(self, text):
        try:
            i = int(text)
            self.tclvar.set(i)
        except:
            self.tclvar.set(0)

class _DropDownField(_ButtonField):
    'A field with dropdown instead of buttons.'
    def get(self):
	try:
	    return str(self.field.choices.index(self.tclvar.get()))
	except:
	    return ''
    def set(self, text):
	try:
	    i = int(text)
	    self.tclvar.set(self.field.choices[i])
	except:
	    self.tclvar.set(self.field.choices[0])

class _BuiltSheet:
    '''A built sheet, holds the frame and the first entry field. It can
    also enable/disable a button if a field on the sheet requires that
    the last line has been visible (i.e., read it all).'''
    def __init__(self, frame):
        self.frame, self.builder, self.first, self.t = frame, None, None, None
    def yview(self, *args):
        'Intercept the scroll command, see if we are at the end.'
        self.t.yview(*args)
        if self.atend():
            self.button['state'] = Tk.NORMAL
            self.button['default'] = 'active'
        else:
            self.button['state'] = Tk.DISABLED
            self.button['default'] = 'normal'
    def intercept(self, t, sb, button):
        sb['command'] = self.yview
        self.t, self.button = t, button
    def intercepting(self):
        return self.t != None
    def atend(self):
        return self.t.yview()[1] == 1.0

class _Wrapper:
    'Wrap a Tk object to look like one of our fields, for use in _Enabler.'
    def __init__(self, w):
	self.widget, self.field = w, None

class _Enabler:
    'A class for when a checkbox enables/disables some entry field(s).'
    def __init__(self, wizard, cb, tclvar, slave):
        # Fields gets set later, on first use, because the entries
        # that we control probably don't exist yet -- they usually
        # appear on the sheet below the controlling checkbox.
        self.tclvar, self.fields, self.wizard = tclvar, [], wizard
        self.slaves = slave.split(',')
        cb['command'] = self.cb_setslaves
    def cb_setslaves(self):
        if len(self.fields) == 0:
            self.fields = [ f for f in self.wizard.allfields
                                if f.field.key in self.slaves ]
	    for f in self.fields[:]:
		self.fields += [ _Wrapper(w) for w in getattr(f, 'kids', []) ]
        if self.tclvar.get() == 0:
            for f in self.fields:
                f.widget['state'] = Tk.DISABLED
                if _isentry(f.field): f.widget['relief'] = Tk.FLAT
        else:
            for f in self.fields:
                f.widget['state'] = Tk.NORMAL
                if _isentry(f.field): f.widget['relief'] = Tk.SUNKEN

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Wizard:
    def __init__(self, sheets, title, root=None, defaults=None, **kw):
        self.current = {}
        if defaults: self.set_defaults(defaults)
        self.numsheets, self.sheetnum, self.showing, self.title = \
	    len(sheets), -1, None, title
        self.enablers = []
        self.kw = kw.copy()
        self.entrywidth = self.kw.get('entrywidth', 40)
        self.whenvalidate = self.kw.get('whenvalidate', atend)
        self.center = self.kw.get('center', 0)
        self.sheetchange = self.kw.get('sheetchange')

        if root:
            self.root = root
	    myroot = 0
        else:
            self.root = Tk.Tk()
            self.root.withdraw()
            self.root.title(title)
            myroot = 1
        R = self.root
        g = self.kw.get('geometry')
        if myroot and g: R.wm_geometry(g)
        R.bind('<Escape>', self._cb_cancel)
        R.bind('<Return>', self._cb_next)
        self.helpobj = self.kw.get('help')
        if self.helpobj: self.helpkey = self.kw.get('helpkey', '<F1>')

        # Some fonts.
        ftdict = self.kw.get('titlefont',
            { 'weight': tkFont.BOLD, 'size': 16, 'family': 'helvetica' })
        self.titlefont = tkFont.Font(**ftdict)
        ftdict = self.kw.get('sheetfont', { 'underline': 1 })
        self.sheetfont = tkFont.Font(**ftdict)

        # Create the buttons before the sheets (see intercept)
        self.fButtons = f = Tk.Frame(R)
        c = 0
        self.bCancel = Tk.Button(f, text='Cancel', width=6,
                            command=self._cb_cancel)
        self.bCancel.grid(row=0, column=c, sticky=Tk.E, padx=10)
        c += 1
        if self.helpobj:
            self.bHelp = Tk.Button(f, text='Help', width=6,
				command=self._cb_help)
            self.bHelp.grid(row=0, column=c, sticky=Tk.E+Tk.W, padx=10)
            c += 1
        self.bBack = Tk.Button(f, text='Back', width=6, command=self._cb_back)
        self.bBack.grid(row=0, column=c, sticky=Tk.E+Tk.W, padx=10)
        c += 1
        self.bNext = Tk.Button(f, text='Next', width=6, command=self._cb_next)
        self.bNext.grid(row=0, column=c, sticky=Tk.W, padx=10)

        # Build the widgets for each sheet, collect all the user-input
        # fields in order.
        self.built, self.allfields = [], []
        for i,s in [ (i, sheets[i]) for i in range(self.numsheets) ]:
            self._build(i, s)

        # Find the biggest sheet, so we can pad out the others.
        maxht, maxwd = 0, 0
        for b in self.built:
            f = b.frame
            f.update_idletasks()
            maxht = max(maxht, f.winfo_reqheight())
            maxwd = max(maxwd, f.winfo_reqwidth())
        self.padybase = 8 + maxht
        self.padxbase = 8 + maxwd

        # Create the title.
        self.fText = Tk.Frame(R)
        self.label = Tk.Label(self.fText, text=title, font=self.titlefont)
        self.label.grid(ipadx=4)

        # Lay out the title, sheets, buttons.
        self.fText.grid(row=0, sticky=Tk.E+Tk.W, pady=4)
        # (the sheets are row 1)
        self.fButtons.grid(row=2, sticky=Tk.E+Tk.W, pady=4)

        if myroot:
            R.deiconify()
            R.resizable(0,0)
            if self.center:
                x = (R.winfo_screenwidth() - R.winfo_reqwidth()) / 2
                y = (R.winfo_screenheight() - R.winfo_reqheight()) / 2
                R.geometry("+%d+%d" % (x,y))
        R.update_idletasks()

    def _build(self, i, s):
        'Build a sheet, creating all the fields in it.'
        f = Tk.Frame(self.root, relief=Tk.RIDGE, borderwidth=1)
        b = _BuiltSheet(f)
        self.built.append(b)

        if isinstance(s, LicenseSheet):
            # Center the title.
            lbl = Tk.Label(f, text=s.title, font=self.sheetfont)
            lbl.grid(row=0, sticky=Tk.E+Tk.W)

            # Insert the text, read-only.
            t = Tk.Text(f)
            if s.ftdict: t['font'] = tkFont.Font(**s.ftdict)
            t['wrap'] = s.wrap
            if not s.file:
                t.insert(0.0, s.text)
            else:
                try:
                    file = open(s.file, 'r')
                    while 1:
                        line = file.readline()
                        if not line: break
                        t.insert(Tk.END, line)
                    file.close()
                except:
                    t.insert(0.0, s.text)
            t.config(height=s.height, width=s.width, state=Tk.DISABLED)
            t.update_idletasks()
            lastline = t.index(Tk.END).split('.')[0]

            t.xview(Tk.MOVETO, "0.0")
            t.yview(Tk.MOVETO, "0.0")
            t.update_idletasks()
	    b.back_text, b.next_text = s.back_text, s.next_text

            # If it doesn't fit, add a scrollbar.
            if int(lastline) < s.height:
                t.grid(row=1, sticky=Tk.N+Tk.S+Tk.E+Tk.W)
            else:
                sb = Tk.Scrollbar(f)
                t['yscrollcommand'] = sb.set
                if s.mustread:
                    b.intercept(t, sb, self.bNext)
                else:
                    sb['command'] = t.yview
                t.grid(row=1, column=0, sticky=Tk.N+Tk.S+Tk.E+Tk.W)
                sb.grid(row=1, column=1, sticky=Tk.N+Tk.S)

            # Horizontal scrollbar wanted?
            if s.hscrollbar:
                sb = Tk.Scrollbar(f, orient=Tk.HORIZONTAL)
                t['xscrollcommand'] = sb.set
                sb['command'] = t.xview
                sb.grid(row=2, column=0, sticky=Tk.E+Tk.W)

        elif isinstance(s, DynamicSheet):
            lbl = Tk.Label(f, text=s.title, font=self.sheetfont)
            lbl.grid(row=0, sticky=Tk.E+Tk.W, pady=4)
            sb = Tk.Scrollbar(f, orient=Tk.VERTICAL)
            t = Tk.Text(f)
            if s.ftdict: t['font'] = tkFont.Font(**s.ftdict)
            t.config(height=s.height, width=s.width, yscrollcommand=sb.set)
            sb['command'] = t.yview
            t.grid(row=1, column=0, sticky=Tk.N+Tk.S+Tk.E+Tk.W)
            sb.grid(row=1, column=1, sticky=Tk.N+Tk.S)
            b.textbox = t
            t.insert(0.0, "\n")
            b.builder = s.builder
	    b.back_text, b.next_text = s.back_text, s.next_text

            # Horizontal scrollbar wanted?
            if s.hscrollbar:
                sb = Tk.Scrollbar(f, orient=Tk.HORIZONTAL)
                t['xscrollcommand'] = sb.set
                sb['command'] = t.xview
                sb.grid(row=2, column=0, sticky=Tk.E+Tk.W)

        elif isinstance(s, Sheet):
            # A 'data entry' sheet.  Most rows have two columns.
            # Center the title.
            lbl = Tk.Label(f, text=s.title, font=self.sheetfont)
            lbl.grid(row=0, sticky=Tk.E+Tk.W, columnspan=2, pady=4)
	    b.back_text, b.next_text = s.back_text, s.next_text

            for field in s.fields:
                if field == None:
                    Tk.Label(f, text='').grid(columnspan=2)
                elif isinstance(field, SpacerField):
                    for j in range(0, field.lines):
                        Tk.Label(f, text='').grid(columnspan=2)
                elif isinstance(field, LabelField):
                    # A label -- just some text.
                    l = Tk.Label(f, text=field.prompt)
                    if field.ftdict:
                        l['font'] = tkFont.Font(**field.ftdict)
                    l.grid(columnspan=2, sticky=field.sticky)
                elif _isentry(field):
                    # A text-entry field. Make a label and an entry area.
                    lbl = Tk.Label(f, text=field.prompt)
                    lbl.grid(column=0, sticky=Tk.W)
                    entry = Tk.Entry(f, width=0 or self.entrywidth)
                    if field.private: entry['show'] = '*'
                    if field.startdisabled: entry['state'] = Tk.DISABLED
                    # Insert the current text, and put the entry on
                    # the same row as the label.
                    entry.insert(0, self.current.get(field.key, ''))
                    r = lbl.grid_info()['row']
                    entry.grid(row=r, column=1, sticky=Tk.E+Tk.W)
                    df = _DataField(self, field, i, entry)
		    df.kids = [lbl]
                    self.allfields.append(df)
                    if self.helpobj: entry.bind(self.helpkey, df.help)
                    if b.first == None: b.first = entry
                    if isinstance(field, FileField):
                        browse = Tk.Button(f, text="...",
                            command=lambda self=self, w=entry: self._fbrowse(w))
                        browse.grid(row=r, column=2, sticky=Tk.W)
			df.kids.append(browse)
                    elif isinstance(field, DirField):
                        browse = Tk.Button(f, text="...",
                            command=lambda self=self, w=entry: self._dbrowse(w))
                        browse.grid(row=r, column=2, sticky=Tk.W)
			df.kids.append(browse)
                elif isinstance(field, CBField):
                    # CheckButton -- on or off.
                    tv = Tk.IntVar()
                    c = Tk.Checkbutton(f, text=field.prompt, variable=tv)
                    c.grid(columnspan=2, sticky=Tk.W)
                    if field.slave:
                        self.enablers.append(_Enabler(self, c, tv, field.slave))
                    bf = _ButtonField(self, field, i, c, tv)
		    bf.kids = [lbl]
                    self.allfields.append(bf)
                    if b.first == None: b.first = c
		elif isinstance(field, DDField):
		    # Dropdown field -- multiple choice.
		    if len(field.choices) == 0: continue
                    lbl = Tk.Label(f, text=field.prompt)
                    lbl.grid(column=0, sticky=Tk.W)
		    tv = Tk.StringVar()
		    om = Tk.OptionMenu(f, tv, *field.choices)
                    r = lbl.grid_info()['row']
		    om.grid(row=r, column=1, sticky=Tk.W+Tk.E)
		    dd = _DropDownField(self, field, i, om, tv)
		    dd.kids = [lbl]
		    self.allfields.append(dd)
                elif isinstance(field, RBField):
                    # Radiobutton -- multiple choice.
                    c = field.choices
                    if len(c) == 0: continue
                    tv = Tk.IntVar()
                    first = None
                    # Create a button for each choice, tying them to
                    # the same variable.
                    for j,prompt in [ (j, c[j]) for j in range(len(c)) ]:
                        rb = Tk.Radiobutton(f, text=prompt, variable=tv,
                                    value=j)
                        rb.grid(sticky=Tk.W)
                        if first == None: first = rb
                    tv.set(self.current.get(field.key, 0))
                    bf = _ButtonField(self, field, i, first, tv)
                    self.allfields.append(bf)
                    if b.first == None: b.first = first
                else:
                    raise TypeError(field.__class__)
        else:
            raise TypeError(s.__class__)

    def _validated(self, fields):
        'Validate a set of fields; return zero on error.'
        # Collect all the values; if any fields take a long time, switch
        # to a "don't rush me" cursor.
        oldcursor = None
        for f in fields:
            self.current[f.key] = f.get()
            if f.field.longvalidate and oldcursor == None:
                oldcursor = self.root['cursor'] or ''
                try:
                    self.root['cursor'] = 'watch'
                except:
                    pass
                self.root.update_idletasks()

        # Call any validators
        errs, firstbad = [], None
        for f in fields:
            v = f.field.validate
            if v:
                try:
                    v.validate(self.current, f.key)
                except InvalidEntry, e:
                    errs.append(e.text)
                    if firstbad == None: firstbad = f
        if oldcursor != None:
            self.root['cursor'] = oldcursor
            self.root.update_idletasks()
        if firstbad:
            # Display all errors, go to the first invalid field.
            tkMessageBox.showerror(self.title, '\n'.join(errs))
            self._goto(firstbad.sheetnum, 0)
            firstbad.widget.focus_set()
            return 0
        return 1

    def set_defaults(self, defaults):
        'Load the default values, a dictionary.'
        self.current = defaults.copy()

    def update_values(self, dict):
	'Update the current set of values with the specified dictionary.'
	self.current.update(dict)
        for f in self.allfields: f.set(self.current.get(f.key, ''))

    def get_values(self):
        for f in self.allfields: self.current[f.key] = f.get()
	return self.current.copy()

    def run(self, start=0):
        'Run through the sheets, collect and validate the values.'
        for f in self.allfields: f.set(self.current.get(f.key, ''))
        for e in self.enablers: e.cb_setslaves()
        self._goto(start)
        self.cancelled = 0
        self.root.wait_window(self.root)
        if self.cancelled: return None
        return self.current

    def _cb_cancel(self, event=None):
        'Cancel method and callback.  Pop back from run().'
        self.cancelled = 1
        self.root.destroy()

    def _cb_back(self, event=None):
        'Callback to handle the "Back" button.'
        self._goto(self.sheetnum - 1)

    def _cb_help(self, event=None):
        'Callback to handle the "Help" button.'
        self.helpobj.sheethelp(self, self.sheetnum)

    def _cb_next(self, event=None):
        'Callback to handle the "Next" button.'
        # Validate this sheet before we try to leave it?
        if self.whenvalidate == persheet and \
               not self._validated([f for f in self.allfields
                                       if f.sheetnum == self.sheetnum]):
            return
        if self.sheetnum == self.numsheets - 1:
            # Leaving the last sheet -- validate everything?
            if self.whenvalidate == persheet or self._validated(self.allfields):
                self.cancelled = 0
                self.root.destroy()
        else:
            self._goto(self.sheetnum + 1)

    def _fbrowse(self, widget):
        'Implement the "Browse" button for a file entry field.'
        name = tkFileDialog.askopenfilename()
        if name:
            widget.delete(0, Tk.END)
            widget.insert(Tk.INSERT, name)

    def _dbrowse(self, widget):
        'Implement the "Browse" button for a Directory entry field.'
        name = askdirectory()
        if name:
            widget.delete(0, Tk.END)
            widget.insert(Tk.INSERT, name)

    def _update_dynamic_content(self, b):
        t = b.textbox
        t['state'] = Tk.NORMAL
        t.delete(0.0, Tk.END)
        t.insert(0.0, "\n")
        for f in self.allfields: self.current[f.key] = f.get()
        b.builder.open(self)
        while 1:
            line = b.builder.readline()
            if not line: break
            t.insert(Tk.END, line)
        b.builder.close()
        t.xview(Tk.MOVETO, "0.0")
        t.yview(Tk.MOVETO, "0.0")
        t.update_idletasks()
        t['state'] = Tk.DISABLED

    def _goto(self, sheetnum, setfocus=1):
        'Start viewing specified sheet.'
        if sheetnum < 0 or sheetnum > self.numsheets: sheetnum = 0
        if self.sheetnum == sheetnum: return
        self.sheetnum = sheetnum
        if self.showing:
            self.showing.grid_forget()
            self.showing = None

        # Get the current sheet, show it.
        b = self.built[self.sheetnum]
        if b.builder:
            self._update_dynamic_content(b)
        f = b.frame
        f.grid(row=1, padx=4, pady=4, sticky=Tk.E+Tk.W+Tk.N+Tk.S,
            ipady=(self.padybase - f.winfo_reqheight() + 1) / 2,
            ipadx=(self.padxbase - f.winfo_reqwidth() + 1) / 2)
        self.showing = f
        if setfocus and b.first: b.first.focus_set()

        # Set the BACK and NEXT buttons appropriately.
        if self.sheetnum == 0:
            self.bBack['state'] = Tk.DISABLED
        else:
            self.bBack['state'] = Tk.NORMAL
	self.bBack['text'] = b.back_text or 'Back'
        if self.sheetnum == self.numsheets - 1:
            self.bNext['text'] = b.next_text or 'Done'
        else:
            self.bNext['text'] = b.next_text or 'Next'
        if b.intercepting() and not b.atend():
            self.bNext['state'] = Tk.DISABLED
            self.bNext['default'] = 'normal'
        else:
            self.bNext['default'] = 'active'

        # Callback
        if self.sheetchange:
            self.sheetchange.goto(self, self.sheetnum)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class HelpPopup:
    def __init__(self):
        pass
    def help(self, wizard, key):
        top = Tk.Toplevel();
        self.top = top
        top.title('Help')
        top.bind('<Return>', self.destroy)
        top.bind('<Escape>', self.destroy)
        text = Tk.Text(top, height=20, width=60)
        sb = Tk.Scrollbar(top, command=text.yview)
        text['yscrollcommand'] = sb.set
        text.grid(row=0, column=0, sticky=Tk.N+Tk.S+Tk.E+Tk.W)
        sb.grid(row=0, column=1, sticky=Tk.N+Tk.S)
        button = Tk.Button(top, text='Dismiss', default='active',
                        command=top.destroy)
        button.grid(row=1, columnspan=2, sticky=Tk.E+Tk.W)
        try:
            self.open(wizard, key)
            while 1:
		l = self.readline()
		if not l: break
                text.insert(Tk.INSERT, l)
	    self.close()
        except:
            text.insert(Tk.INSERT, 'Sorry, no additional help is available.\n')
        text['state'] = Tk.DISABLED
        wizard.root.wait_window(top)

    def destroy(self, event=None):
        self.top.destroy()

    def sheethelp(self, wizard, sheetnum):
        self.help(wizard, 'sheet%d' % sheetnum)

    def open(self, wizard, key): pass
    def readline(self): pass
    def close(self): pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

copyright = """
                        COPYRIGHT
                        ---------

Copyright 2001, Zolera Systems, Inc.
All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or
sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, provided that the above copyright notice(s) and
this permission notice appear in all copies of the Software and that
both the above copyright notice(s) and this permission notice appear in
supporting documentation.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF THIRD PARTY RIGHTS. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS
INCLUDED IN THIS NOTICE BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT
OR CONSEQUENTIAL DAMAGES, OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE
OR PERFORMANCE OF THIS SOFTWARE.

Except as contained in this notice, the name of a copyright holder
shall not be used in advertising or otherwise to promote the sale, use
or other dealings in this Software without prior written authorization
of the copyright holder.
"""

if __name__ == '__main__': print copyright
