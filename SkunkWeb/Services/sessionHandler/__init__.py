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
# $Id: __init__.py,v 1.1.1.1 2001/08/05 15:00:07 drew_csillag Exp $
# Time-stamp: <01/05/04 13:25:03 smulloni>
########################################################################
# session handling package

import os

def __initFlag():
    import SkunkWeb.ServiceRegistry as reg
    reg.registerService('sessionHandler')

def __initConfig():
    from SkunkWeb import Configuration
    Configuration.mergeDefaults(
        # session timeout, in seconds. 
        SessionTimeout = 30*60,
        
        # the key under which the session is kept
        SessionIDKey='sessionID',
        
        # the host, user, password, and database (for MySQLSessionStoreImpl)
        SessionHandler_MySQLHost='localhost',
        SessionHandler_MySQLUser='sessionHandler',
        SessionHandler_MySQLPass='sessionPass',
        SessionHandler_MySQLDB='sessionStore',
        
        # table, id column, session value column, and timestamp column
        # (for MySQLSessionStoreImpl)
        SessionHandler_MySQLTable='Sessions',
        SessionHandler_MySQLIDColumn='id',
        SessionHandler_MySQLPickleColumn='pickle',
        SessionHandler_MySQLTimestampColumn='accessTime',

        # directory where pickle files are stored (for FSSessionStore)
        SessionHandler_FSSessionDir=os.path.join(Configuration.SkunkRoot, 'var/run/skunksessions')
        
        # reap interval (in seconds).  A negative value, or zero,
        # will turn off reaping.  it would be reasonable for at most
        # one server to reap any given session store.
        SessionReapInterval=300,
        SessionStore=None
        )

def __initSession():
    import SkunkWeb.Configuration as Configuration
    if not Configuration.SessionStore:
        LOG("no sessionStore defined: cannot load sessionHandler service")
    else:
        import Session
        import SkunkWeb.constants as skc
        import SkunkWeb.Hooks as hk
        import requestHandler.requestHandler as rr
        hk.ServerStart.append(Session.mungeConnection)
        rr.PostRequest.addFunction(Session.saveSession, "%s*" % skc.WEB_JOB)

########################################################################
    
__initFlag()

__initConfig()

__initSession()


########################################################################
# $Log: __init__.py,v $
# Revision 1.1.1.1  2001/08/05 15:00:07  drew_csillag
# take 2 of import
#
#
# Revision 1.12  2001/08/02 02:10:37  smulloni
# minor cleanup.
#
# Revision 1.11  2001/07/25 13:34:31  smulloni
# modified sessionHandler so that the SessionStore parameter is a string, not
# a class; added comments to sw.conf.in for sessionHandler-related goodies.
#
# Revision 1.10  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.9  2001/05/04 18:38:51  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.8  2001/04/25 20:18:46  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.7  2001/04/16 17:53:00  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.6  2001/04/04 18:11:35  smullyan
# KeyedHooks now take glob as keys.  They are tested against job names with
# fnmatch.fnmatchcase.   The use of '?' is permitted, but discouraged (it is
# also pointless).  '*' is your friend.
#
# Revision 1.5  2001/04/04 14:46:29  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
# Revision 1.4  2001/04/02 15:06:38  smullyan
# fixed some typos.
#
# Revision 1.3  2001/04/02 00:54:18  smullyan
# modifications to use new requestHandler hook mechanism.
#





