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
# $Id: __init__.py,v 1.8 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/05/04 11:31:32 smulloni>
# fundamental service for handling single requests.
########################################################################

def __initFlag():
    from SkunkWeb import ServiceRegistry
    ServiceRegistry.registerService('requestHandler')

def __initConfig():
    from SkunkWeb import Configuration
    Configuration.mergeDefaults(DocumentTimeout=30,
                                PostResponseTimeout=20,
                                job=None)

__initFlag()
__initConfig()


########################################################################
# $Log: __init__.py,v $
# Revision 1.8  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.7  2001/05/04 18:38:50  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.6  2001/04/25 20:18:45  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.5  2001/04/23 17:30:07  smullyan
# basic fixes to basic auth and httpd; added KeepAliveTimeout to requestHandler,
# using select().
#
# Revision 1.4  2001/04/23 04:55:46  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.3  2001/04/04 20:00:17  smullyan
# The configuration setting, DocumentTimeout, was being used in requestHandler
# while its default was being set in templating_experimental -- fixed.  The
# alarm is now reset after the response is set, and a PostResponseTimeout
# takes over for the remaining two hooks.
#
# Revision 1.2  2001/04/04 14:46:28  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
########################################################################

