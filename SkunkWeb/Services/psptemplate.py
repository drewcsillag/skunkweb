#  
#  Copyright (C) 2002 Drew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################
from SkunkWeb import Configuration, ServiceRegistry, Hooks
from SkunkWeb.LogObj import DEBUG

Configuration.mergeDefaults(pspTemplateTypes=[], pspTopLevelInterpret=1)

ServiceRegistry.registerService('psptemplate')
PSP=ServiceRegistry.PSPTEMPLATE

from DT import DT_REGULAR, DT_DATA, DT_INCLUDE
import AE.Cache
import AE.CodeSources
import AE.Executables
import psp

PSP_CACHEFILE_VERSION = 1

def _pspCompileFunc( name, data ):
    return psp.psp_compile( data, name )

def getPSPCode( name, srcModTime ):
    return AE.Cache._getCompiledThing( name, srcModTime, 'psptemplate',
                                       _pspCompileFunc,
                                       PSP_CACHEFILE_VERSION )

    
class PSPExecutable(AE.Executables.PythonExecutable):
    def __init__(self, name, compType, srcModTime):
        self.name = name
        self.code_obj, self.text = getPSPCode( name, srcModTime )
        self.compType = compType
        AE.CodeSources.putSource( name, self.text )

def _installExecutables():
    d = {
        ('application/x-psp-python-component', DT_INCLUDE) : PSPExecutable,
        ('application/x-psp-python-component', DT_REGULAR) : PSPExecutable,
        ('application/x-psp-python-data-component', DT_DATA) : PSPExecutable,
        }
    AE.Executables.executableByTypes.update(d)
    DEBUG(PSP, "exebytype= %s" % AE.Executables.executableByTypes)
    for i in Configuration.pspTemplateTypes:
        for j in (DT_INCLUDE, DT_REGULAR, DT_DATA):
            AE.Executables.executableByTypes[(i,j)] = PSPExecutable

_installExecutables()
if Configuration.pspTopLevelInterpret:
    Configuration.interpretMimeTypes.append(
        'application/x-psp-python-component')
