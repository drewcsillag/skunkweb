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
# $Id: __init__.py,v 1.1.1.1 2001/08/05 15:00:11 drew_csillag Exp $
# Time-stamp: <01/05/04 13:07:01 smulloni>
########################################################################

# load web and ae_component services, upon which templating depends.
import web 
import ae_component


def __initFlag():
    from SkunkWeb import ServiceRegistry
    ServiceRegistry.registerService('templating')

def __initTags():
    from AE.Cache import tagRegistry
    import ArgsTag
    tagRegistry.addTag(ArgsTag.ArgsTag())
    import LogTags
    for i in LogTags.LoggingTags:
        tagRegistry.addTag(i)
    import SendmailTag
    tagRegistry.addTag(SendmailTag.SendmailTag())
    import HTMLTags
    for i in ['UrlTag', 'ImageTag', 'FormTag', 'HiddenTag', 'RedirectTag']:
        tagRegistry.addTag(getattr(HTMLTags, i)())
    
def _formatException(exc_text, sessionDict):
    return exc_text

def __initHooks():
    import SkunkWeb.constants as skc
    import Handler
    from web.protocol import HandleConnection
    from aecgi import RequestFailed
    jobGlob=skc.TEMPLATING_JOB+'*'
    HandleConnection.addFunction(Handler.requestHandler, jobGlob)
    HandleConnection.addFunction(Handler.plainHandler, jobGlob)
    HandleConnection.addFunction(Handler.fourOhFourHandler, jobGlob)
    RequestFailed.addFunction(_formatException, jobGlob)



########################################################################

__initFlag()
__initHooks()
__initTags()

import SkunkWeb.LogObj
SkunkWeb.LogObj.LOG("templating service loaded")

########################################################################
# $Log: __init__.py,v $
# Revision 1.1.1.1  2001/08/05 15:00:11  drew_csillag
# take 2 of import
#
#
# Revision 1.18  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.17  2001/05/04 18:38:51  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.16  2001/04/25 20:18:49  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.11  2001/04/23 04:55:48  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.10  2001/04/20 21:49:53  smullyan
# first working version of http server, still more rough than diamond.
#
# Revision 1.9  2001/04/10 22:48:29  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
# Revision 1.8  2001/04/04 20:00:18  smullyan
# The configuration setting, DocumentTimeout, was being used in requestHandler
# while its default was being set in templating_experimental -- fixed.  The
# alarm is now reset after the response is set, and a PostResponseTimeout
# takes over for the remaining two hooks.
#
# Revision 1.7  2001/04/04 19:14:20  smullyan
# abstracted AE component initialization into the ae_component service;
# removed the equivalent functionality from templating_experimental,
# and modified templating_experimental and remote to import ae_component
# and invoke its hooks (by altering their jobNames).
#
# Revision 1.6  2001/04/04 18:11:35  smullyan
# KeyedHooks now take glob as keys.  They are tested against job names with
# fnmatch.fnmatchcase.   The use of '?' is permitted, but discouraged (it is
# also pointless).  '*' is your friend.
#
# Revision 1.5  2001/04/04 14:46:30  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
# Revision 1.4  2001/04/02 22:31:42  smullyan
# bug fixes.
#
# Revision 1.3  2001/04/02 15:06:39  smullyan
# fixed some typos.
#
# Revision 1.2  2001/04/02 00:02:53  smullyan
# integration of new hook framework (in requestHandler.hooks) into
# web_experimental and templating_experimental services.
# 




