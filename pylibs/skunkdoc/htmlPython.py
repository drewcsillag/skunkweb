#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import string
from scanners import common
from htmlCommon import *
from docStringHTMLRenderer import renderDocString

MODULE_COLOR="#ddddff"
CLASS_COLOR="#ffccff"

def writeModules(index, modules, destPath, nav, ns):
    #if more than MAX... modules have their own index page, otherwise
    #normal CT index page
    if len(modules) > MAX_TOC_ENTRIES_BEFORE_SEPARATE:
        nav = nav.newPlusAlter(up = 'module_index.html', upText = 'Module Index')

    for module in index['code'].values():
        _writeModule(destPath, module, index, nav, ns)

def _writeItemToc(module, out, pfx=''):
    if not pfx and module.subModules:
        out('<BR><B>Sub Modules</B><BR>')
        for mod in module.subModules:
            out('&nbsp;&nbsp;<A HREF="m.%s.html">%s</A><BR>' % (
                mod.name, string.split(mod.name, '.')[-1]))
    classes = filter(lambda x: x.__class__.__name__ == 'Class',
                     module.funcClasses)
    functions = filter(lambda x: x.__class__.__name__ == 'Function',
                     module.funcClasses)

    if len(functions) > 5:
        out("<BR><B>Functions</B><BR>")
        for f in functions:
            out('&nbsp;&nbsp;<A HREF="m.%s%s.html#%s">%s</A><BR>' % (
                pfx, module.name, f.name, f.name))
    if len(classes) > 5:
        out("<BR><B>Classes</B><BR>")
        for c in classes:
            out('&nbsp;&nbsp;<A HREF="m.%s%s.%s.html">%s</A><BR>' % (
                pfx, module.name, c.name, c.name))

def _writeFunction(func, out, toppath = ''):
    """**take a function definition and produce HTML"""
    out('<P><A NAME="%s">' % func.name)
    out('<B><CODE>%s</CODE></B><BR>' % func.sig)
    out('<p><font size=-1>%s</font>' % renderDocString(func.docString))
    out('<HR>')

def _writeInherits(upThing, klass, out, index, ns):
    if klass.bases:
        out('<B>inherits from:</B>')
        l = []
        for k in klass.bases:
            try:
                scns = ns.getNamespace(upThing.name)
                bp = scns[k]
                l.append('<CODE><A HREF="m.%s.html">%s</A></CODE>' % (
                    bp.name, k))
            except KeyError:
                l.append('<CODE>%s</CODE>' % k)
        out(string.join(l, ', '))
            
def _writeClass(destPath, upThing, klass, nav, index, ns, toppath = ''):
    out = writer(open(destPath + '/m.%s%s.%s.html' % (
        upThing.name, toppath, klass.name), 'w'))
    nav = nav.newPlusAlter(up = 'm.%s%s.html' % (upThing.name, toppath),
                           upText = '%s <code>%s</code>' % (
                               upThing.__class__.__name__,
                               upThing.name))
    out('<HTML><HEAD><TITLE>Class %s</TITLE></HEAD>\n' % klass.name)
    out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
    out('<H2>Class %s</H2>' % common.plainEscape(klass.name))
    out(nav.render(1))
    out('<HR><TABLE CELLSPACING=10 BORDER=0 width=100%><TR>')
    out('<TD COLSPAN=2 BGCOLOR=%s>' % CLASS_COLOR)
    out('<H2>Class <code>%s</code></H2>' % klass.name)
    _writeInherits(upThing, klass, out, index, ns)
    out('<font size=-1>%s</font>' % renderDocString(klass.docString))
    _writeItemToc(klass, out, '%s%s.' % (toppath, upThing.name))
    out('</TD></TR>')
    out('<TR><TD BGCOLOR=%s><FONT COLOR=%s>---</font></TD><TD>' % (
        CLASS_COLOR, CLASS_COLOR))

    for item in klass.funcClasses:
        if item.__class__.__name__ == 'Function':
            _writeFunction(item, out)
        else: #it's a class
            out('<B>Class <A HREF="m.%s%s.%s.html">%s</A></B><BR>' % (
                toppath, klass.name, item.name, item.name))
            _writeClass(destPath, klass, item, nav, index, ns,
                        '%s%s.' % (toppath, klass.name))

    
    out('</TD></TR></TABLE><BR><HR>')
    out(nav.render(0))
    out('</BODY></HTML>')

def _writeModule(destPath, module, index, nav, ns):
    out = writer(open(destPath + '/m.%s.html' % module.name, 'w'))
    out('<HTML><HEAD><TITLE>Module %s</TITLE></HEAD>\n' % module.name)
    out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
    out('<H2>Module %s</H2>' % common.plainEscape(module.name))
    out(nav.render(1))
    out('<TD COLSPAN=2 BGCOLOR=%s>' % MODULE_COLOR)
    out('<HR><TABLE CELLSPACING=10 BORDER=0 width=100%><TR>')
    out('<TD COLSPAN=2 BGCOLOR=%s>' % MODULE_COLOR)
    out('<H2>Module <code>%s</code></H2>' % module.name)
    out('<font size=-1>%s</font>' % renderDocString(module.docString))
    _writeItemToc(module, out)
    out('</TD></TR>')
    out('<TR><TD BGCOLOR=%s><FONT COLOR=%s>----</font></TD><TD>' % (
        MODULE_COLOR, MODULE_COLOR))

    for item in module.funcClasses:
        if item.__class__.__name__ == 'Function':
            _writeFunction(item, out)
        else: #it's a class
            out('<B>Class <A HREF="m.%s.%s.html">%s</A></B><BR>' % (
                module.name, item.name, item.name))
            _writeClass(destPath, module, item, nav, index, ns)

    out('</TD></TR></TABLE><HR>')
    out(nav.render(0))
    out('</BODY></HTML>')
