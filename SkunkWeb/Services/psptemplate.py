#  
#  Copyright (C) 2002 Drew Csillag <drew_csillag@yahoo.com>
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
# $Id: aecgi.py,v 1.3 2002/07/19 16:21:02 smulloni Exp $
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
