#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
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
import globals
import common
import os
import types
import sys
import string

def _findImports(co):
    """find and return the import statements in the code object"""

    #the bulk of this is stolen/modified/hacked/etc. from dis.py
    #opcodes
    IMPORT_NAME = 107
    IMPORT_FROM = 108
    STORE_NAME = 90
    HAVE_ARGUMENT = 90 
    STORE_FAST = 125

    code = co.co_code
    imports = []
    n = len(code)
    i = 0
    while i < n:
        op = ord(code[i])
        i = i + 1
        
        #if got an import opcode
        if op == IMPORT_NAME:
            #get the oparg to get the moduleName
            oparg = ord(code[i]) + ord(code[i+1])*256
            moduleName = co.co_names[oparg]
            #advance to next opcode
            i = i + 2
            op = ord(code[i])
            #if a store opcode, just a plain import
            if op == STORE_NAME or op == STORE_FAST:
                imports.append((moduleName, None))
            #else, it's a from foo import x,x,x,x
            elif op == IMPORT_FROM:
                names = []

                while op == IMPORT_FROM:
                    #get name
                    i = i + 1
                    oparg = ord(code[i]) + ord(code[i+1])*256
                    names.append(co.co_names[oparg])
                    #advance to next opcode
                    i = i + 2
                    op = ord(code[i])

                imports.append((moduleName, names))

        #not an import, but has an argument, skip past the arg
        elif op >= HAVE_ARGUMENT:
            i = i + 2
    return imports

def _getKind( sig ):
    """**determine whether sig refers to class or a function (def)"""
    foo = string.split(string.strip(sig))
    return foo[0]

def _getDef(lines, firstLineNo):
    """**try to intelligently find the signature given a
    <code>firstLineNo</code> and the text lines in the document.  Basically,
    look for an open parenthesis and find the matching close parenthesis.  If
    we don't find an open parenthesis, stop when we hit a :
    """
    
    parenCount = 0
    seenFirst = 0
    line = lines[ firstLineNo ]
    usedLines = 0
    index = 0

    #if we've seen an open paren and haven't found the close paren
    while parenCount or not seenFirst:
        #if we see a colon before the first open paren, we're done
        if line[index] == ':' and not seenFirst:
            break
        elif line[index] == '(':
            seenFirst = 1
            parenCount = parenCount + 1
        elif line[index] == ')':
            parenCount = parenCount - 1
        index = index + 1
        #if we were at (or past) the end of the line, grab and append
        #the next line
        if index >= len(line):
            usedLines = usedLines + 1
            line = line + lines[ firstLineNo + usedLines ]
    return string.join(string.split(line[:index]))


class Function:
    def __init__(self, co, lines, sig):
        self.name = co.co_name
        self.sig = sig
        self.imports = _findImports(co)
        self.docString = common.doDocString(co.co_consts[0])

class ClassModuleBase:
    def __init__(self, co, lines):
        self.co = co
        self.lines = lines

    def getCodeThings(self):
        l = []
        co = self.co
        for item in co.co_consts:
            if type(item) == types.CodeType and item.co_name[0] != '_':
                l.append((item.co_name, item))

        #sort stuff in sorted order with classes at the top
        l.sort(self._sortFunc)
        return l
    
    def _sortFunc(self, x, y):
        xkind = _getKind( _getDef( self.lines, x[1].co_firstlineno - 1) )
        ykind = _getKind( _getDef( self.lines, y[1].co_firstlineno - 1) )
        if xkind != ykind:
            return -cmp(xkind, ykind)
        return cmp(x[0], y[0])

    def doCodeThings(self, codeThings):
        self.funcClasses = []
        for name, co in codeThings:
            sig = _getDef(self.lines, co.co_firstlineno - 1)
            kind = _getKind(sig)
            if kind == 'class':
                self.funcClasses.append(Class(co, self.lines, sig))
            elif kind == 'def':
                if co.co_name != '<lambda>':
                    self.funcClasses.append(Function(co, self.lines, sig))

        
class Class(ClassModuleBase):
    def __init__(self, co, lines, sig):
        ClassModuleBase.__init__(self, co, lines)
        self.name = co.co_name
        self.sig = sig
        self.imports = _findImports(co)
        paren = string.find(sig, '(')
        if paren == -1:
            self.bases = []
        else:
            basesString = sig[ paren+1:-1 ]
            self.bases = string.split(basesString, ',')
            self.bases = map(string.strip, self.bases)
        self.docString = common.doDocString(co.co_consts[0])
        codeThings = self.getCodeThings() # should sort
        self.doCodeThings(codeThings)        

class Module(ClassModuleBase):
    def __repr__(self):
        return '<Module %s>' % self.name
    
    def __init__(self, moduleName, filename):
        self.name = moduleName
        self.text = text = open(filename).read()
        if text == '\0':
            co = compile('', filename, 'exec')
        else:
            text = string.join(string.split(text, '\r\n'), '\n')
            co = compile(text+'\n', filename, 'exec')
        self.co = co
        #do effectively lines = StringIO.StringIO(text).readlines(), but faster
        self.lines = map(lambda x: x+'\n', string.split( text, '\n' ))

        ClassModuleBase.__init__(self, co, self.lines)
        self.subModules = []
        self.imports = _findImports(co)
        self.getDocString()
        codeThings = self.getCodeThings() # should sort
        self.doCodeThings(codeThings)

    def getDocString(self):
        co = self.co
        #how to check for module doc strings in the code object is a bit
        #trickier than functions and classes since it's not just co_consts[0]
        if (co.co_consts[0] and type(co.co_consts[0]) == type('')
            and len(co.co_names) and co.co_names[0] == '__doc__'): 
            self.docString = common.doDocString(co.co_consts[0])
        else:
            self.docString = common.doDocString('')

class BustedModule(Module):
    def __init__(self, mn, filename):
        self.name = mn
        self.text = open(filename).read()
        self.subModules = []
        self.imports = []
        self.docString = common.doDocString('THIS MODULE DID NOT PARSE!!')
        self.funcClasses = []
        
def doDir(dirPath, modPath=''):
    l = os.listdir(dirPath)
    if modPath != '' and '__init__.py' not in l:
        return []
    l.sort()
    modules = []
    thisPkgModule = None
    for filename in l:
        fullFilename = '%s/%s' % (dirPath, filename)
        if (os.path.isfile(fullFilename)
            and filename[-3:] == '.py'):
            if filename == '__init__.py':
                thisPkgModule = Module(modPath, fullFilename)
            else:
                if modPath == '':
                    modName = filename[:-3]
                else:
                    modName = '%s.%s' % (modPath, filename[:-3])
                try:
                    mod = Module(modName, fullFilename)
                except SyntaxError, v:
                    if globals.VERBOSE:
                        print 'module %s failed to compile' % modName
                        print v.filename, v.lineno, v.text, v.offset
                    globals.ERRORS.append('module %s failed to compile' %
                                          modName)
                    globals.ERRORS.append('%s %s %s %s' % (
                        v.filename, v.lineno, v.text, v.offset))
                    mod = BustedModule(modName, fullFilename)
                    #mod = None
                if mod:
                    if globals.VERBOSE:
                        print 'done doing %s' % modName
                    modules.append(mod)
        elif (os.path.isdir(fullFilename)):
            if modPath == '':
                newModPath = filename
            else:
                newModPath = '%s.%s' % (modPath, filename)
            mod = doDir(fullFilename, newModPath)
            if mod:
                modules.append(mod)
            
    if thisPkgModule != None and modPath != '':
        thisPkgModule.subModules = modules
        return thisPkgModule
    else:
        return modules
    
if __name__ == '__main__':
    #mods = doDir('/home/drew/devel/nskdoc')
    #mods = doDir('/home/drew/devel/support.skunk.org/site-libs')
    pass
