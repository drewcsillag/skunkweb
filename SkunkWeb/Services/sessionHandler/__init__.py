#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# $Id: __init__.py,v 1.7 2003/05/01 20:45:54 drew_csillag Exp $
# Time-stamp: <01/05/04 13:25:03 smulloni>
########################################################################
# session handling package

import os

def __initFlag():
    import SkunkWeb.ServiceRegistry as reg
    reg.registerService('sessionHandler')

def __initConfig():
    import SkunkWeb.Configuration
    import SkunkWeb.confvars
    SkunkWeb.Configuration.mergeDefaults(
        # session timeout, in seconds. 
        SessionTimeout = 30*60,
        
        # the key under which the session is kept
        SessionIDKey='sessionID',

        SessionHandler_SQLTable='Sessions',
        SessionHandler_SQLIDColumn='id',
        SessionHandler_SQLPickleColumn='pickle',
        SessionHandler_SQLTimestampColumn='accessTime',
        
        # the MySQL connection alias 
        SessionHandler_MySQLAlias='session',
        
        # the same, for PostgreSQL
        SessionHandler_PostgreSQLAlias="session",
        
        # directory where pickle files are stored (for FSSessionStore)
        SessionHandler_FSSessionDir=os.path.join(SkunkWeb.confvars.LOCALSTATEDIR,
                                                 'skunksessions'),
        
        # reap interval (in seconds).  A negative value, or zero,
        # will turn off reaping.  it would be reasonable for at most
        # one server to reap any given session store.
        SessionReapInterval=300,
        SessionStore=None,
        )

def __initSession():
    import SkunkWeb.Configuration as Configuration
##    if not Configuration.SessionStore:
##        import SkunkWeb.LogObj as lo
##        lo.LOG("no sessionStore defined: cannot load sessionHandler service")
##    else:
    import Session
    import SkunkWeb.constants as skc
    import SkunkWeb.Hooks as hk
    import requestHandler.requestHandler as rr
    hk.ServerStart.append(Session.mungeConnection)
    allweb="%s*" % skc.WEB_JOB
#    rr.InitRequest.addFunction(Session.untouch, allweb)
    rr.PostRequest.addFunction(Session.saveSession, allweb)

########################################################################
    
__initFlag()

__initConfig()

__initSession()


