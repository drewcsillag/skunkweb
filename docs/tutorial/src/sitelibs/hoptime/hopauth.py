# Time-stamp: <02/11/10 14:01:32 smulloni>

"""
support for authenticating hoptime users
against the hoptime database.
"""

import auth as A
import hopapi as H
import AE.Component
import SkunkWeb.Configuration as C
import cPickle
import base64

class HoptimeAuth(A.CookieAuthBase, A.RespAuthBase):
    def __init__(self, loginPage):
        A.RespAuthBase.__init__(self, loginPage)
        A.CookieAuthBase.__init__(self,
                                  'hoptime_auth',
                                  'Ingabook Forsmythe',
                                  {'path' : '/'})

    def validate(self, username, password):
        user=H.Users.getUnique(username=username)
        # return the actual user object as a true value --
        # will be returned by A.CookieAuthBase.checkCredentials,
        # in our checkCredentials, below, and stored in the
        # CONNECTION object
        if user and user['password']==password:
            return user

    def checkCredentials(self, conn):
        user=A.CookieAuthBase.checkCredentials(self, conn)
        if user:
            conn.hoptimeUser=user
            return 1
        conn.hoptimeUser=None
        return 0
        
    def authFailed(self, conn):
        conn.remoteUser='guest'
        conn.remotePassword=None
        if C.HoptimeRequireValidUser:
            A.RespAuthBase.authFailed(self, conn)

    def login(self, conn, username, password):
        authorized=A.CookieAuthBase.login(self, conn, username, password)
        conn.hoptimeUser=authorized
        return authorized



### user-space function -- can be called from templates
##def process_auth(conn, username, password, vals=None):
##    """
##    processes login.  conn is a HttpConnection object;
##    username, password, and vals should be taken from
##    conn.args (using whatever forms keys are employed).
##    Four outcomes:
##       if the argument vals in not none and the ahuth check
##          is ok, raise OK
##       if vals is not true and 
##    """
##    # don't allow GET logins
##    if conn.method=='POST' and None not in (username, password):
##        authorized=A.getAuthorizer().login(conn,
##                                           username,
##                                           password)
##        if authorized:
##            conn.hoptimeUser=authorized
##            if vals:
##                conn.args=cPickle.loads(base64.decodestring(vals))
##                raise A.OK
##            return 1
##        return 0
##    return -1
