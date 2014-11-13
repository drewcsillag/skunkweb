#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
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
#                                job=None)
                                )

__initFlag()
__initConfig()


########################################################################
# $Log: __init__.py,v $
# Revision 1.2  2003/05/01 20:45:54  drew_csillag
# Changed license text
#
# Revision 1.1.1.1  2001/08/05 15:00:05  drew_csillag
# take 2 of import
#
#
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

