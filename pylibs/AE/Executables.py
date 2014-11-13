#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sys
import cStringIO
import copy

from SkunkExcept import *
from DT import DT_REGULAR, DT_DATA, DT_INCLUDE, DTExcept

import MimeTypes
import Cache
import CodeSources
import Exceptions

import cfg
#config vars
cfg.Configuration.mergeDefaults(
    templateMimeTypes = ['text/html', 'text/plain']
    )
#/config

#init funcs == initTemplateMimeTypes()

# Component signature stuff - used by the <:compargs:> checking stuff
_SIG_META        = 'comp_signature'
_SIG_REQUIRED    = 'required'
_SIG_HAS_DEFAULT = 'has_default'
_SIG_SPILLOVER   = 'spillover'

class dummy:
    pass

_hidden_namespace = dummy() # for templates

# class ExecutableThing:
#     def __init__( self, name, compType, srcModTime ):
#     def mergeNamespaces( self, namespace, argDict, auxVars ):
#     def run( self ):
#         return output

class PythonExecutable:
    def __init__(self, name, compType, srcModTime):
        self.name = name
        self.code_obj, self.text  = Cache.getPythonCode( name, srcModTime )
        self.compType = compType
        CodeSources.putSource( name, self.text )

    def mergeNamespaces( self, namespace, argDict, auxVars ):
        namespace['ReturnValue'] = Exceptions.ReturnValue
        namespace.update(auxVars)
        namespace.update(argDict)
        if self.compType != DT_DATA:
            namespace['__name__'] = '__main__'
        self.namespace = namespace
        return namespace
    
    def run( self ):
        oldstdout = sys.stdout
        if self.compType in ( DT_REGULAR, DT_INCLUDE ):
            outputIO = sys.stdout = cStringIO.StringIO()

        try:
            try:
                exec self.code_obj in self.namespace, self.namespace
            except Exceptions.ReturnValue, val:
                if self.compType != DT_DATA:
                    raise
                try:
                    return val.args[0]
                except (IndexError,AttributeError):
                    return val
                
            except DTExcept.DTHaltError:
                pass
                
            if self.compType in ( DT_REGULAR, DT_INCLUDE ):
                output = outputIO.getvalue()
                return output

        finally:
            if self.compType in ( DT_REGULAR, DT_INCLUDE ):
                sys.stdout = oldstdout #sys.__stdout__

class STMLExecutable:
    def __init__(self, name, compType, srcModTime):
        self.name = name
        self.dt = Cache.getDT( name, srcModTime )
        self.compType = compType
        CodeSources.putSource( name, self.dt._text )

    def mergeNamespaces( self, namespace, argDict, auxVars ):
        sig = self.dt.meta().get(_SIG_META)
        if sig:
        #check the argument signature here if a <:compargs:> tag
            namespace.update(auxVars)
            for v in sig[_SIG_REQUIRED]:
                if not argDict.has_key(v) and not auxVars.has_key(v):
                    raise SkunkStandardError, (
                        'component %s: argument %s: expected but not passed' %
                        (self.name, v))
                elif argDict.has_key(v):
                    namespace[v] = argDict[v]
                    del argDict[v]
                #else: #in auxVars
            for arg in sig[_SIG_HAS_DEFAULT]:
                if argDict.has_key(arg):
                    namespace[arg] = argDict[arg]
                    del argDict[arg]

            if sig[_SIG_SPILLOVER]:
                namespace[sig[_SIG_SPILLOVER]] = argDict
            elif argDict:
                raise SkunkStandardError, (
                    "component %s: extra arguments encountered: %s" %
                    (self.name,
                     ', '.join(argDict.keys())))
                
            self.namespace = namespace
            return namespace
        else:
            namespace.update(auxVars)
            namespace.update(argDict)
            self.namespace = namespace
            return namespace
            
    def run( self ):
        hns = copy.copy(_hidden_namespace)
        hns.OUTPUT = cStringIO.StringIO()

        oldstdout = sys.stdout
        sys.stdout = hns.OUTPUT
        try:
            return self.dt(self.namespace, self.namespace,
                           hns, self.compType)
        finally:
            sys.stdout = oldstdout #sys.__stdout__
        
executableByTypes = {
    ("text/x-stml-component",             DT_INCLUDE) : STMLExecutable,
    ("text/x-stml-component",             DT_REGULAR) : STMLExecutable,
    ("text/x-stml-data-component",        DT_DATA)    : STMLExecutable,
    ("text/x-stml-include",               DT_INCLUDE) : STMLExecutable,

    ("application/x-python",              DT_INCLUDE) : PythonExecutable,
    ("application/x-python",              DT_REGULAR) : PythonExecutable,
    ("text/x-stml-python-component",      DT_REGULAR) : PythonExecutable,
    ("text/x-stml-python-data-component", DT_DATA)    : PythonExecutable,
    ("text/x-stml-python-include",        DT_INCLUDE) : PythonExecutable,
    }

def initTemplateMimeTypes():
    for i in cfg.Configuration.templateMimeTypes:
        for j in (DT_INCLUDE, DT_REGULAR, DT_DATA):
            executableByTypes[(i,j)] = STMLExecutable
        
def getExecutable( name, compType, srcModTime ):
    mimeType = MimeTypes.getMimeType( name )
    try:
        
        if executableByTypes.has_key((mimeType, compType)):
            exe = executableByTypes[mimeType, compType]
        elif mimeType in cfg.Configuration.templateMimeTypes:
            exe = STMLExecutable
        else:
            raise KeyError, (mimeType, compType)

    except KeyError, val:
        raise SkunkStandardError, \
              "No executable form for %s servicing %s (%s)" % (
                  mimeType, name, {
                      DT_INCLUDE:"INCLUDE",
                      DT_REGULAR:"REGULAR",
                      DT_DATA:"DATA"
                      }[compType])
    return exe(name, compType, srcModTime)
