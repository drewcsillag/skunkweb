# $Id: ConfigAdditives.py,v 1.3 2001/10/02 02:35:34 smulloni Exp $
# Time-stamp: <02/03/30 14:22:41 smulloni>
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>,
#                     Jacob Smullyan <smulloni@smullyan.org>
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

########################################################################

__all__=['Location',
         'Host',
         'Port',
         'IP',
         'UNIXPath',
         'Scope',
         'Include']

from SkunkWeb.Hooks import ServerStart
import scopeable as scope
import ConfigLoader
import KickStart

def _createMatcher(matcherClass, paramName, paramVal, kids, kw):
    m=matcherClass(paramName, paramVal, kw)
    if kids:
        m.addChildren(*kids)
    return m

def Location(path, **kw):
    return _createMatcher(scope.SimpleStringMatcher,
                          'location',
                          path,
                          None,
                          kw)

def Host(hostname, *kids, **kw):
    return _createMatcher(scope.GlobMatcher,
                          'host',
                          hostname,
                          kids,
                          kw)

def Port(port, *kids, **kw):
    return _createMatcher(scope.StrictMatcher,
                          'port',
                          port,
                          kids,
                          kw)

def IP(ip, *kids, **kw):
    return _createMatcher(scope.StrictMatcher,
                          'ip',
                          ip,
                          kids,
                          kw)

def UNIXPath(path, *kids, **kw):
    return _createMatcher(scope.GlobMatcher,
                          'unixpath',
                          path,
                          kids,
                          kw)                       

def Scope(*scopeMatchers):
    from SkunkWeb import Configuration
    Configuration.addScopeMatchers(*scopeMatchers)

def Include(filename):
    ConfigLoader.loadConfigFile(filename, KickStart.CONFIG_MODULE)
        
def importConfiguration():
    # have to do this here since this is imported before the configuration
    # "module" has been put in place
    global Configuration
    from SkunkWeb import Configuration    


ServerStart.append(importConfiguration)


########################################################################
# $Log: ConfigAdditives.py,v $
# Revision 1.3  2001/10/02 02:35:34  smulloni
# support for scoping on unix socket path; very serious scope bug fixed.
#
# Revision 1.2  2001/09/09 02:37:41  smulloni
# performance enhancements, removal of sundry nastinesses and erasure of
# reeking rot.
#
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
# Revision 1.11  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.10  2001/05/04 18:38:52  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.9  2001/05/03 17:26:12  smullyan
# added an IP pseudo-directive to SkunkWeb.ConfigAdditives; Host now matches
# strictly (perhaps it should be a glob); port and ip are now put in
# sessionDict by requestHandler; HTTPConnection's "host" field is now the host
# header, if any, with the port removed.
#
# Revision 1.8  2001/05/03 16:14:59  smullyan
# modifications for scoping.
#
# Revision 1.7  2001/05/01 23:03:39  smullyan
# added support for name-based virtual hosts.
#
########################################################################
