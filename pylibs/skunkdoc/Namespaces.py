#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""below here is where we figure out where classes/functions and modules come
from so we can (among other things) find base class locations"""
from scanners import globals
import sys
import string
from UserDict import UserDict

class Namespace(UserDict):
    """**represents a very skeletal form of a regular python namespace"""
    def __init__(self, name = '', kind = 'module', ispkg = 0):
        UserDict.__init__(self)
        self.imports = {'plain': [], 'from': []}
        self.activated = 0
        self.ispkg = ispkg
        self.name = name
        self.kind = kind
        
    def getNamespace(self, name):
        """**gets a subnamespace by the name <code>name</code>"""
        ns = self
        for i in string.split(name,'.'):
            ns = ns[i]
        return ns

    def getImportNamespace(self, name):
        """**return a namespace the way import does.
        <p/> i.e. <code>import foo.bar</code> returns the <code>foo</code>
        namespace, not the <code>foo.bar</code> namespace
        """
        try:
            topName = string.split(name,'.')[0]
        except TypeError:
            globals.ERRORS.append('name is %s'% name)
            raise
        
        self.getNamespace(name) #check to see that it exists
        return self[topName]
    
    def makeNamespace(self, name, ispkg=0):
        """**creates and returns a subnamespace by the name
        <code>name</code>"""
        ns = self

        bits = string.split(name)
        for i in range(len(bits)):
            key = bits[i]
            if not ns.has_key(key):
                ns[key] = Namespace(string.join(bits[:i+1],'.'))
            ns.ispkg = 1 #assumption
            ns = ns[key]
            
        return ns

    def subModules(self):
        """**locates all of the submodules directly below self"""
        return map(lambda x:x[0],
                   filter(lambda (x, y):isinstance(y, Namespace),
                          self.items()))

    def __str__(self):
        return self.name

def _makeNames(modObj, modName, ns):
    for i in modObj.funcClasses:
        itemName = '%s.%s' % (modName, i.name)
        if i.__class__.__name__ == 'Class':
            newns = ns[i.name] = Namespace(itemName, 'class')
            _makeNames(i, i.name, newns)
        else: #function
            ns[i.name] = Namespace(itemName, 'function')

def _doImports(namespaces, modObj):
    fromImports = filter(lambda x:x[1] is not None, modObj.imports)
    plainImports = filter(lambda x:x[1] is None, modObj.imports)
    ns = namespaces.getNamespace(modObj.name)
    ns.imports = {
        'from': fromImports,
        'plain': plainImports,
        }

def _activateImports(namespaces, modName, recurList = []):
    """**affect the imports in the namespaces and attempt to be smart about
    it, but failling gracefully if stuff can't be found
    """
    if modName in recurList: # if we run into ourselves
        return
    
    #print 'activating', modName, recurList
    modNs = namespaces.getNamespace(modName)
    modNs.activated = 1
    imports = modNs.imports

    modNameStuff = string.split(modName, '.')

    #get current package name, if applicable
    if len(modNameStuff) > 1:
        pkg = string.join(modNameStuff[:-1],'.')
    elif modNs.ispkg:
        pkg = modName
    else:
        pkg = ''

    #do regular style imports
    #print 'imports=', imports, modNs.name, modNs.kind
    for p in imports['plain']:
        gotIt = 0
        if pkg: # if in a package, try package local
            try:
                midns = namespaces.getNamespace(pkg)
                target = midns.getImportNamespace(p[0])
                gotIt = 1
            except KeyError:
                pass

        if not gotIt:
            try:
                target = namespaces.getImportNamespace(p[0])
                gotIt = 1
            except KeyError:
                pass

        impRoot = string.split(p[0],'.')[0]
        if gotIt:
            modNs[impRoot] = target

    #do "from x import ylist" imports
    for targetModName, names in imports['from']:
        #boy this seems largely familliar <0.3 wink>
        #ok, locate the module
        gotIt = 0
        if pkg: # if in a package, try package local
            try:
                targetName = '%s.%s' % (pkg, targetModName)
                target = namespaces.getNamespace(targetName)
                gotIt = 1
            except KeyError:
                pass

        if not gotIt:
            try:
                targetName = targetModName
                target = namespaces.getNamespace(targetModName)
                gotIt = 1
            except KeyError:
                pass

        impRoot = string.split(targetModName,'.')[0]
        if gotIt: #ok found the module namespace
            #activate its imports
            _activateImports(namespaces, targetName, recurList + [modName])
            #if get everything, set names to everything in there
            if '*' in names:
                names = target.keys()
                
            #fetch the stuff out
            for name in names:
                if target.has_key(name): #if the namespace has the name
                    modNs[name] = target[name] # do it


def getNamespaces(index):
    namespaces = Namespace()
    for modName, moduleObj in index['code'].items():
        splits = string.split(modName, '.')
        for i in range(1,len(splits)+1):
            ns = namespaces.makeNamespace(string.join(splits[:i]))
        _makeNames(moduleObj, modName, ns)

    for modName, modObj in index['code'].items():
        try:
            _doImports(namespaces, modObj)
        except:
            if globals.VERBOSE:
                print 'error encountered processing module %s' % modName
                print '%s:%s' % (sys.exc_type, sys.exc_value)
            globals.ERRORS.append('error encountered processing module %s'
                                  % modName)
            globals.ERRORS.append('%s:%s' % (sys.exc_type, sys.exc_value))

    for modName in index['code'].keys():
        _activateImports(namespaces, modName)
    return namespaces
