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
# $Id: __init__.py,v 1.1.1.1 2001/08/05 14:59:58 drew_csillag Exp $
# Time-stamp: <01/05/04 11:09:09 smulloni>

# a rewrite of the web service, using requestHandler.
# inventory:
#    protocol.AecgiProtocol extends requestHandler.protocol.Protocol 
#    protocol.HTTPConnection : a connection object (request and response rolled into one)
#                              for templating engines


#WEB_JOB="/web/"



def __initFlag():
    from SkunkWeb import ServiceRegistry
    ServiceRegistry.registerService('web', 'WEB')
    import SkunkWeb.Configuration as C
    C.mergeDefaults(mergeQueryStringWithPostData=1)
    
def __initHooks():
    import requestHandler.requestHandler
    import protocol
    import SkunkWeb.constants

    jobGlob=SkunkWeb.constants.WEB_JOB+'*'
    requestHandler.requestHandler.HandleRequest[jobGlob]=protocol._processRequest
    requestHandler.requestHandler.CleanupRequest[jobGlob]=protocol._cleanupConfig

__initFlag()
__initHooks()

        
########################################################################
# $Log: __init__.py,v $
# Revision 1.1.1.1  2001/08/05 14:59:58  drew_csillag
# take 2 of import
#
#
# Revision 1.8  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.7  2001/05/04 18:38:52  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.6  2001/04/25 20:18:53  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.6  2001/04/04 18:11:36  smullyan
# KeyedHooks now take glob as keys.  They are tested against job names with
# fnmatch.fnmatchcase.   The use of '?' is permitted, but discouraged (it is
# also pointless).  '*' is your friend.
#
# Revision 1.5  2001/04/04 14:46:31  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
# Revision 1.4  2001/04/02 00:02:53  smullyan
# integration of new hook framework (in requestHandler.hooks) into
# web_experimental and templating_experimental services.
#
# Revision 1.3  2001/04/01 07:27:34  smullyan
# after various wacky experiments, moved a prototype of a new hook
# implementation into requestHandler.hooks.py.
#
# Revision 1.2  2001/03/29 23:02:26  smullyan
# annotated job.py with indications of grandiose plans.  Job integration.
#
# Revision 1.1  2001/03/29 20:17:14  smullyan
# experimental, non-working code for requestHandler and derived services.
#





