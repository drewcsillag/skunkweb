#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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
# $Id: __init__.py,v 1.12 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/05/04 17:39:07 smulloni>
# support for remote calls from other SkunkWeb servers using a
# python-specific protocol.
########################################################################

import ae_component
import requestHandler
from SkunkWeb import constants, ServiceRegistry, Configuration


def __initFlag():
    ServiceRegistry.registerService('remote')

def __initHandler():
    # TEMPORARILY HARD-CODED IN constants.py
    #skc.REMOTE_JOB=.rc.AE_COMPONENT_JOB + "/remote/"
    jobGlob='*%s*' % constants.REMOTE_JOB
    import handler
    requestHandler.requestHandler.HandleRequest[jobGlob]=handler.handleRequestHookFunc
    

def __initConnections():
    from protocol import SkunkWebRemoteProtocol
    Configuration.mergeDefaults(RemoteListenPorts=['TCP:localhost:9887'])
    if Configuration.RemoteListenPorts:
        requestHandler.requestHandler.addRequestHandler(SkunkWebRemoteProtocol(),
                                                        Configuration.RemoteListenPorts)
        
__initFlag()  
__initHandler()
__initConnections()

########################################################################
# $Log: __init__.py,v $
# Revision 1.12  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.11  2001/05/04 21:37:12  smullyan
# another typo... guess I should take a nap.
#
# Revision 1.10  2001/05/04 18:38:49  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.9  2001/04/24 21:43:02  smullyan
# fixed bug in httpd.protocol (was accidentally removing line return after
# HTTP response line, producing weirdness).  Removed call of deprecated
# method of config object in remote.__init__.py; added list of configuration
# variables that need to be documented to sw.conf.in.
#
# Revision 1.8  2001/04/16 17:52:59  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.7  2001/04/04 19:14:20  smullyan
# abstracted AE component initialization into the ae_component service;
# removed the equivalent functionality from templating_experimental,
# and modified templating_experimental and remote to import ae_component
# and invoke its hooks (by altering their jobNames).
#
# Revision 1.6  2001/04/04 18:11:34  smullyan
# KeyedHooks now take glob as keys.  They are tested against job names with
# fnmatch.fnmatchcase.   The use of '?' is permitted, but discouraged (it is
# also pointless).  '*' is your friend.
#
# Revision 1.5  2001/04/04 16:28:01  smullyan
# CodeSources.py wasn't calling the installIntoTraceback function; fixed.
# Remote service now handles exceptions better.  Code equivalent to that in
# test.py will need to become part of the templating_experimental service.
#
# Revision 1.4  2001/04/04 14:46:28  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
# Revision 1.3  2001/04/02 15:06:37  smullyan
# fixed some typos.
#
# Revision 1.2  2001/04/02 00:54:16  smullyan
# modifications to use new requestHandler hook mechanism.
#
# Revision 1.1  2001/03/29 20:17:07  smullyan
# experimental, non-working code for requestHandler and derived services.
#
########################################################################
