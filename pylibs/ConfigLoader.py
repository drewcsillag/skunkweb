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
# $Id: ConfigLoader.py,v 1.2 2001/09/04 18:25:38 smulloni Exp $
# Time-stamp: <01/05/02 15:31:50 smulloni>
########################################################################

import os, sys, types
import scopeable as scope

class ScopeableConfig(scope.Scopeable):
    # for backwards compatability. This layer
    # may be eliminated!!!! TO BE DONE

    _mergeDefaults=scope.Scopeable.mergeDefaults
    _mergeDefaultsKw=scope.Scopeable.mergeDefaults
    _trim=scope.Scopeable.trim
    _mash=scope.Scopeable.mash
    _update=scope.Scopeable.update
    _mashSelf=scope.Scopeable.mashSelf
    _push=scope.Scopeable.push
    _pop=scope.Scopeable.pop
    
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
        
    exec codeObj in ns, ns #let caller catch exc's
    
    if not cfMod:
        m = sys.modules[cfgModuleName] = ScopeableConfig(ns)
        l = cfgModuleName.split('.')
        if len(l) > 1:
            setattr(__import__('.'.join(l[:-1]),['*'], ['*'], ['*']), l[-1], m)

########################################################################
# $Log: ConfigLoader.py,v $
# Revision 1.2  2001/09/04 18:25:38  smulloni
# modified so as to use scopeable pylib
#
# Revision 1.1.1.1  2001/08/05 15:00:26  drew_csillag
# take 2 of import
#
#
# Revision 1.7  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.6  2001/05/03 16:15:00  smullyan
# modifications for scoping.
#
# Revision 1.5  2001/05/01 21:46:29  smullyan
# introduced the use of scope.Scopeable to replace the the ConfigLoader.Config
# object.
#
# Revision 1.4  2001/04/10 22:48:32  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
########################################################################
