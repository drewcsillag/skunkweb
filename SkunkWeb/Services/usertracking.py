########################################################################
# Time-stamp: <03/03/11 18:02:16 smulloni>
#
# Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
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
########################################################################

"""
provides cookie-based usertracking, for logging packages
like WebTrends.

Perhaps this should also (optionally) perform logging,
rather than relying on apache to do it.... TBD
"""

from SkunkWeb import Configuration, ServiceRegistry
from uuid import uuid
import time

ServiceRegistry.registerService('usertracking')
USERTRACKING=ServiceRegistry.USERTRACKING

_cookie_attrs=('path',
               'expires',
               'domain',
               'comment',
               'version',
               'max-age')

_config_attrs=tuple([("usertrackingCookie%s" % \
                      x.replace('-', '_').capitalize(), x) \
                     for x in _cookie_attrs])

Configuration.mergeDefaults(
    # whether usertracking is on
    usertrackingOn=0,
    # whether Configuration.usertrackingCookieExpires is an
    # absolute timestamp, or an interval to be added to the
    # current time (the latter is the default)
    usertrackingExpiresAbsolute=0,
    # function to generate unique ids; should take one argument,
    # the CONNECTION.  If None, a uuid will be generated.
    usertrackingGenUIDFunc=None,
    # function to verify a usertracking cookie;
    # by default, None
    usertrackingVerifyCookieFunc=None,
    # values for cookie parameters
    usertrackingCookiePath=None,
    usertrackingCookieExpires=None,
    usertrackingCookieDomain=None,
    usertrackingCookieComment=None,
    usertrackingCookieVersion=None,
    usertrackingCookieMax_age=None)

def _verify_cookie(conn, cookiename):
    if conn.requestCookie.has_key(cookiename):
        v=conn.requestCookie[cookiename]
        f=Configuration.usertrackingVerifyCookieFunc
        if f is not None:
            return f(v)
        return 1
    return 0
    
def _add_usertracking_cookie(conn, sessionDict):
    if Configuration.usertrackingOn:
        cookiename=Configuration.usertrackingCookieName
        if not _verify_cookie(conn, cookiename):
            f=Configuration.usertrackingGenUIDFunc
            if f is None:
                conn.responseCookie[cookiename]=uuid()
            else:
                conn.responseCookie[cookiename]=f(conn)
            morsel=conn.responseCookie[cookiename]
            for c, a in _config_attrs:
                if a=='expires':
                    # special case
                    if not Configuration.usertrackingExpiresAbsolute:
                        v=getattr(Configuration, c)
                        if v is not None:
                            morsel[a]=v+time.time()
                        continue
                v=getattr(Configuration, c)
                if v is not None:
                morsel[a]=v


def WebtrendsCookie(conn):
    """\
    generates an id of the format remote_ip-timestamp.
    This can be used as Configuration.usertrackingGenUIDFunc.
    The default uuid function is more unique, actually.

    Note -- the webtrends apache module (binary only)
    claims in its documentation that this is its format,
    but the webtrends website makes a different claim
    (it says it logs the time since January 1st, 1601
    -- what for?). Since I don't see any point in using
    this format, I don't really care.
    """
    return "%s-%0.6f" % (conn.env['REMOTE_ADDR'], time.time())

def _inithooks():
    import web.protocol
    import SkunkWeb.constants
    jobGlob="*%s*" % SkunkWeb.constants.WEB_JOB
    web.protocol.PreHandleConnection.addFunction(_add_usertracking_cookie, jobGlob)

_inithooks()
