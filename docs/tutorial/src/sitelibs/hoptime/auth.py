# Time-stamp: <02/10/02 18:45:50 smulloni>
# $Id$

"""
support for authenticating hoptime users
against the hoptime database.
"""

import auth as A
import hopapi as H

class HoptimeDBAuthBase:
    """
    base class for validation of users
    against the hoptime Users table.
    """
    def validate(self, username, password):
        user=H.Users.getUnique(username=username)
        # return the actual user object as a true value
        if user and user['password']==password:
            return user

class HoptimeUserSessionBase(A.SessionAuthBase):
    """
    subclass of auth.SessionAuthBase that
    stores the Users object in the session
    """
    def login(self, conn, username, password):
        user=self.validate(username, password)
        if user:
            sess=conn.getSession(1)
            sess[self.usernameSlot]=user
            sess.save()
            return 1

class CookieHoptimeAuth(A.CookieAuthBase,
                    HoptimeDBAuthBase,
                    A.RespAuthBase):
    """
    a session-free authorizer
    """
    def __init__(self, cookieName, nonce, extras, loginPage):
        A.CookieAuthBase.__init__(self, cookieName, nonce, extras)
        HoptimeDBAuthBase.__init__(self)
        A.RespAuthBase.__init__(self, loginPage)

class SessionHoptimeAuth(HoptimeUserSessionBase,
                     HoptimeDBAuthBase,
                     A.RespAuthBase):
    """
    a session authorizer
    """
    def __init__(self, usernameSlot, loginPage):
        HoptimeUserSessionBase.__init__(self, usernameSlot)
        HoptimeDBAuthBase.__init__(self)
        A.RespAuthBase.__init__(self, loginPage)
