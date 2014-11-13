#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>,
#                     Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

__all__=['Location',
         'File',
         'Host',
         'Port',
         'ServerPort',
         'IP',
         'UNIXPath',
         'Scope',
         'Include']

from SkunkWeb.Hooks import ServerStart
import scope
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

def File(path, **kw):
    return _createMatcher(scope.RegexMatcher,
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

def ServerPort(port, *kids, **kw):
    return _createMatcher(scope.StrictMatcher,
                          'server_port',
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
