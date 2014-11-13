########################################################################
# Time-stamp: <2007-08-26 15:33:54 smulloni>
#
# Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

r"""
provides cookie-based usertracking, for logging packages
like WebTrends.

Perhaps this should also (optionally) perform logging,
rather than relying on apache to do it.... TBD

If you want to log this cookie inside apache, but don't want to log
every single cookie the client might send, this apache configuration
will be helpful if you are using Apache 1.3.x. (You can already do
this with Apache 2.0 using the "%{COOKIENAME}C" log format}.  Assuming
that the default cookie name, SKUNKTREK_ID, is in use, put this in
some appropriate place in your apache conf files:

  RewriteEngine On
  RewriteCond %{HTTP_COOKIE} SKUNKTREK_ID=([^;]+)
  RewriteRule .* [E=SKUNKTREK_ID:%1]

This creates an environmental variable with the same value as the
usertracking cookie; this will get passed to SkunkWeb, but is perfectly
harmless.  Then log using a log format like this:

  LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %{SKUNKTREK_ID}e" cookie-combined

Note that this only logs *incoming* cookies.  This means that clients who
don't accept cookies won't generate spurious usertracking ids in the apache
logs, which is apparently a problem with apache's mod_usertrack.
"""

from SkunkWeb import Configuration, ServiceRegistry
from SkunkWeb.LogObj import DEBUG
try:
    from uuid import uuid
except ImportError:
    from uuid import uuid4
    def uuid():
        return str(uuid4())
import time
import Cookie

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
    # name of the cookie
    usertrackingCookieName="SKUNKTREK_ID",
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
                            morsel[a]=Cookie._getdate(v)
                        continue
                v=getattr(Configuration, c)
                if v is not None:
                    morsel[a]=v
            DEBUG(USERTRACKING, str(morsel))
            DEBUG(USERTRACKING, str(conn.responseCookie[cookiename]))


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
