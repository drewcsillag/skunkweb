#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sys

#config vars
import cfg
cfg.Configuration._mergeDefaultsKw(
    debugFile = None,
    debugFlags = 0,
    accessFile = sys.stderr,
    errorFile = sys.stderr,
    logFile = sys.stderr
    )
#/config

(COMPONENT, COMPONENT_TIMES, MEM_COMPILE_CACHE, CACHE,
 WEIRD, COMPONENT_TTL) = [2**i for i in range(6)]
names = {
    COMPONENT: 'COMPONENT',
    CACHE: 'CACHE',
    COMPONENT_TIMES: 'COMPONENT_TIMES',
    MEM_COMPILE_CACHE: "MEMCACHE",
    WEIRD: "WEIRD",
    COMPONENT_TTL: 'COMPONENT_TTL',
    }

def DEBUG(kind, msg):
    if not cfg.Configuration.debugFile:
        return
    if cfg.Configuration.debugFlags & kind:
        cfg.Configuration.debugFile.write("%s: %s\n" % (names[kind], msg))
        cfg.Configuration.debugFile.flush()

def DEBUGIT(kind):
    if not cfg.Configuration.debugFile:
        return
    if cfg.Configuration.debugFlags & kind:
        return 1
    
def ACCESS(msg):
    if not cfg.Configuration.accessFile:
        return
    cfg.Configuration.accessFile.write("%s\n" % msg)

def ERROR(msg):
    if not cfg.Configuration.errorFile:
        return
    cfg.Configuration.errorFile.write("%s\n" % msg)

def LOG(msg):
    if not cfg.Configuration.logFile:
        return
    cfg.Configuration.logFile.write("%s\n" % msg)
    
