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
    
