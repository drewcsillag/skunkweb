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
# $Id: ServiceRegistry.py,v 1.7 2001/07/28 15:45:16 drew Exp $
# Time-stamp: <01/04/16 14:07:47 smulloni>
########################################################################
import Logger

registeredServices={}
_flags={}
_n=0

def getDebugServices():
    debugServices=[]
    for service, flagname in registeredServices.items():
        #if Logger.debugFlags.intValue & eval(flagname):
        if Logger.debugFlags & eval(flagname):
            debugServices.append(service)
    return debugServices

def registerService(serviceName, flagName=None):
    
    if not flagName:
        flagName=serviceName.upper()
    import sys
    if not registeredServices.has_key(serviceName):        
        registeredServices[serviceName]=flagName
        import ServiceRegistry
        newFlag=1<<ServiceRegistry._n
        setattr(ServiceRegistry, flagName, newFlag)
        _flags[newFlag]=serviceName
        _flags[flagName]=serviceName
        ServiceRegistry._n+=1

def __initFlags():
    for coreService in ['component',
                        'component_times',
                        'mem_compile_cache',
                        'cache',
                        'weird',
                        'component_ttl',
                        'core',
                        'user']:
                        
        registerService(coreService)
        

def debugRegisteredServices(services):
    """
    creates the debugFlag
    """

    import operator
    import sys
    _debugServices=[x for x in services if registeredServices.has_key(x)]
    recognized=[registeredServices[x] for x in _debugServices]

    if len(recognized):
        debugFlag=reduce(operator.or_, map(eval, recognized))
    else:
        debugFlag=0


    # I haven't exported the actual type yet from mmint -- TO BE DONE
    #if type(Logger.debugFlags).__name__=='MMInt':
    #    Logger.debugFlags.intValue=debugFlag
    #else:
    Logger.debugFlags=debugFlag

def getSourceFromKind(kind):
    """
    dropped into the Logger module to replace the function of the same name,
    this simply maps debug flags with service names
    """
    return _flags.get(kind, None)


__initFlags()

########################################################################    
# $Log: ServiceRegistry.py,v $
# Revision 1.7  2001/07/28 15:45:16  drew
# no longer uses shared memory for debug flags
#
# Revision 1.6  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.5  2001/04/16 18:10:16  smullyan
# fix to reload in Server.py; debug flags in AE module now reconciled with
# ServiceRegistry.
#
# Revision 1.4  2001/04/11 21:23:29  smullyan
# removed some stderr print statements.
#
# Revision 1.3  2001/04/11 20:47:11  smullyan
# more modifications to the debugging system to facilitate runtime change of
# debug settings.  Segfault in mmint.c fixed (due to not incrementing a
# reference count in the coercion method).
#
# Revision 1.2  2001/04/10 22:48:31  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
# Revision 1.1  2001/03/29 20:19:36  smullyan
# added ServiceRegistry to keep list of registered services and compute their
# debug flags at registration time.
#
########################################################################
