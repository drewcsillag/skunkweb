#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################
import Logger
import sys

registeredServices={}
_flags={}
_n=0

def getDebugServices():
    debugServices=[]
    for service, flagname in registeredServices.items():
        if Logger.debugFlags & eval(flagname):
            debugServices.append(service)
    return debugServices

def registerService(serviceName, flagName=None):
    
    if not flagName:
        flagName=serviceName.upper()
    if not registeredServices.has_key(serviceName):        
        registeredServices[serviceName]=flagName
        global _n
        global _flags
        newFlag=1<<_n
        globals()[flagName]=newFlag
        _flags[newFlag]=serviceName
        _flags[flagName]=serviceName
        _n+=1

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

    Logger.debugFlags=debugFlag

def getSourceFromKind(kind):
    """
    dropped into the Logger module to replace the function of the same name,
    this simply maps debug flags with service names
    """
    return _flags.get(kind, None)


__initFlags()

