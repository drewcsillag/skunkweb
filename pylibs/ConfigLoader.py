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
# $Id: ConfigLoader.py,v 1.6 2003/04/18 04:08:22 smulloni Exp $
# Time-stamp: <01/05/02 15:31:50 smulloni>
########################################################################

import os, sys, types
import scope 
    
def loadConfigFile(filename, cfgModuleName):
    filename = os.path.abspath(filename)
    loadConfigString(open(filename).read(), filename, cfgModuleName)

def loadConfigString(s, filename, cfgModuleName):
    try:
        co = compile(s, filename, 'exec')
    except SyntaxError:
         sys.stderr.write("syntax error in config file!\n")
         sys.exc_value.filename = filename # fix filename bit from <string>
         raise
    else:
        loadConfig(co, cfgModuleName)
                                         
def loadConfig(codeObj, cfgModuleName):
    cfMod = sys.modules.get(cfgModuleName)
    ns = cfMod and cfMod.defaults() or {}

    # we used to exec in ns, ns; anyone see a problem with this?
    exec codeObj in {}, ns  #let caller catch exc's

    if cfMod:
        cfMod.update(ns)
    else:
        m = sys.modules[cfgModuleName] = scope.Scopeable(ns)
        l = cfgModuleName.split('.')
        if len(l) > 1:
            setattr(__import__('.'.join(l[:-1]),['*'], ['*'], ['*']), l[-1], m)
