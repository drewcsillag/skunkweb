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
# $Id: protocol.py,v 1.3 2001/09/04 19:12:57 smulloni Exp $
# Time-stamp: <01/05/04 15:57:35 smulloni>
########################################################################

from SkunkExcept import SkunkCriticalError
from SkunkWeb.LogObj import DEBUG, logException
from SkunkWeb.ServiceRegistry import WEB
from SkunkWeb import Configuration, ConfigAdditives, constants
from requestHandler.protocol import Protocol, PreemptiveResponse
import Cookie
import Date
import SocketScience
import cStringIO
import cgi
import marshal
import sys
import time
import types
import browser
from SkunkWeb.Hooks import KeyedHook

headersOnlyMethods=['HEAD'] 
headersOnlyStatuses=[100, 101, 102, 204, 304]

HaveConnection=KeyedHook()
PreHandleConnection=KeyedHook()
HandleConnection=KeyedHook()


class HTTPConnection:
    '''
    The connection object used for HTTP, passed to various web hooks.
    '''
    def __init__(self, requestData):
        self._output=cStringIO.StringIO()
        self.env = requestData['environ']
        self._requestDict=requestData
        self._status=200
        self._stdin = requestData['stdin']
        self._initURI(self.env)
        self._initArgs(requestData)
        self._initHeaders()
        self._initCookies()
        
        self.browser = browser.Browser(self.requestHeaders.get('User-Agent'))
        # for convenience -- possibly expand this, possibly eliminate it
        self.method=self.env['REQUEST_METHOD']
        
        # possibly this field, although harmless, should not be here,
        # the extraction of the port-less host should be done
        # in _processRequest -- CONSIDER ***
        fullHost=self.requestHeaders.get("Host", "")
        # get rid of port, it confuses matching by host
        colindex=fullHost.find(':')
        if colindex!=-1:
            fullHost=fullHost[:colindex]
        self.host=fullHost

    def write(self, s):
        self._output.write(s)
        
    def _initArgs(self, requestData):
        oldstdin=sys.stdin
        sys.stdin = cStringIO.StringIO(requestData['stdin'])
        query = cgi.FieldStorage(environ = requestData['environ'])
        sys.stdin = oldstdin
        self.args=self._convertArgs(query)
       
    def _convertArgs(self, query):
        d = {}
        for k in query.keys():
            d[k] = self._convertArg(query[k])
        return d

    def _convertArg(self, val):
        if type(val) in (types.ListType, types.TupleType):
            return map(self._convertArg, val)
        if val.filename:
            return _File(val)
        return val.value        

    def _initHeaders(self):
        self.requestHeaders = HeaderDict(self._requestDict['headers'])
        self.responseHeaders = HeaderDict({
            'Server': 'SkunkWeb %s' % Configuration.SkunkWebVersion,
            'Date': str(Date.HTTPDate(time.time())),
            'Status': '200 OK'
            })

    def _initCookies(self):
        self.requestCookie = Cookie.SimpleCookie()
        if self.requestHeaders.has_key('Cookie'):
            self.requestCookie.load(self.requestHeaders['Cookie'])
        self.responseCookie = Cookie.SimpleCookie()        

    def _initURI(self, env):
        self.uri=self.realUri = env.get('SCRIPT_NAME', '') + env.get('PATH_INFO', '')

    def setContentType(self, type):
        self.responseHeaders['Content-Type'] = type
        
    def response(self):
        rawOutput, headers = self._output.getvalue(), ''
        if not self.responseHeaders.has_key('Content-Length'):
            self.responseHeaders['Content-Length'] = len(rawOutput)
        if self.responseCookie.keys():
            headers = headers + str(self.responseCookie) + '\r\n'
        for i in self.responseHeaders.items():
            headers = headers + "%s: %s\r\n" % i
        if self.method in headersOnlyMethods or self._status in headersOnlyStatuses:
            return headers+"\r\n"
        else:
            return headers + "\r\n" + rawOutput
    
    def setStatus(self, status):
        try:
            self.responseHeaders['Status'] = _http_statuses[status]
        except KeyError:
            raise SkunkCriticalError, 'invalid status: %s' % status
        self._status = status
        
    def redirect(self, url):
        self.responseHeaders['Location'] = url
        self.setStatus(301)
        self._output=NullOutput()
        DEBUG(WEB, "Redirecting to %s" % url)
        
########################################################################

class _File:
    def __init__(self, val):
        self.contents, self.filename = val.value, val.filename

    def __str__(self):
        return 'Uploaded file %s -- use obj.contents to get contents' % self.filename

########################################################################
    
class Redirect(Exception):
    pass

########################################################################

class NullOutput:
    def write(self, *args): pass
    def getvalue(self):
        return ''

########################################################################
import skunklib
class HeaderDict:
    '''
    dictionary class that stores headers and formats them consistently.
    '''
    def __init__(self, initval={}):
        self._fixHeader = skunklib.normheader
        self._d = {}
        for k, v in initval.items():
            self._d[self._fixHeader(k)] = v

    def __getitem__(self, d):
        return self._d[self._fixHeader(d)]

    def __setitem__(self, k, v):
        self._d[self._fixHeader(k)] = v

    def __repr__(self):
        return repr(self._d)

    def has_key(self, k):
        return self._d.has_key(k)

    def get(self, k, default=None):
        return self._d.get(k, default)

    def items(self):
        return self._d.items()

    def _fixHeader(self, s):
        '''
        utility function for formatting headers in a consistent manner.
        '''
        return '-'.join([i.capitalize() for i in s.split('-')])

########################################################################

#
# The verbose status table
#
_http_statuses = { 
 100: '100 Continue',
 101: '101 Switching Protocols',
 102: '102 Processing',
 200: '200 OK',
 201: '201 Created',
 202: '202 Accepted',
 203: '203 Non-Authoritative Information',
 204: '204 No Content',
 205: '205 Reset Content',
 206: '206 Partial Content',
 207: '207 Multi-Status',
 300: '300 Multiple Choices',
 301: '301 Moved Permanently',
 302: '302 Found',
 303: '303 See Other',
 304: '304 Not Modified',
 305: '305 Use Proxy',
 306: '306 unused',
 307: '307 Temporary Redirect',
 400: '400 Bad Request',
 401: '401 Authorization Required',
 402: '402 Payment Required',
 403: '403 Forbidden',
 404: '404 Not Found',
 405: '405 Method Not Allowed',
 406: '406 Not Acceptable',
 407: '407 Proxy Authentication Required',
 408: '408 Request Time-out',
 409: '409 Conflict',
 410: '410 Gone',
 411: '411 Length Required',
 412: '412 Precondition Failed',
 413: '413 Request Entity Too Large',
 414: '414 Request-URI Too Large',
 415: '415 Unsupported Media Type',
 416: '416 Requested Range Not Satisfiable',
 417: '417 Expectation Failed',
 418: '418 unused',
 419: '419 unused',
 420: '420 unused',
 421: '421 unused',
 422: '422 Unprocessable Entity',
 423: '423 Locked',
 424: '424 Failed Dependency',
 500: '500 Internal Server Error',
 501: '501 Method Not Implemented',
 502: '502 Bad Gateway',
 503: '503 Service Temporarily Unavailable',
 504: '504 Gateway Time-out',
 505: '505 HTTP Version Not Supported',
 506: '506 Variant Also Negotiates',
 507: '507 Insufficient Storage',
 508: '508 unused',
 509: '509 unused',
 510: '510 Not Extended'}

########################################################################

def _processRequest(requestData, sessionDict):
    """
    request handling functioning for requestHandler's
    HandleRequest hook.
    """
    response=None
    
    DEBUG(WEB, 'creating Connection')
    DEBUG(WEB, 'requestData is %s' % str(requestData))
    connection=HTTPConnection(requestData)

    sessionDict[constants.CONNECTION]=connection
    sessionDict[constants.HOST]=connection.host
    sessionDict[constants.LOCATION]=connection.uri
    try:
        DEBUG(WEB, 'executing HaveConnection hook')
        HaveConnection(Configuration.job, connection, sessionDict)
        DEBUG(WEB, 'survived HaveConnection hook')

        # overlay of config information
        Configuration.trim()
        Configuration.scope(sessionDict)
        #Configuration.saveMash()

        DEBUG(WEB, 'executing PreHandleConnection hook')
        PreHandleConnection(Configuration.job, connection, sessionDict)
                
    except PreemptiveResponse, pr:
        DEBUG(WEB, 'got preemptive response')
        response=pr.responseData
    except:
        logException()
    else:
        DEBUG(WEB, 'handling connection')
        HandleConnection(Configuration.job, connection, sessionDict)
        response=connection.response()

    # the connection should be available to postResponse and cleanup hooks.
    sessionDict[constants.CONNECTION]=connection
    DEBUG(WEB, 'returning response: %s' % response)
    DEBUG(WEB, 'length of response: %d' % len(response))
    return response


def _cleanupConfig(requestData, sessionDict):
    """
    function for requestHandler's CleanupRequest hook
    """
    if sessionDict.has_key(constants.HOST):
        del sessionDict[constants.HOST]
    if sessionDict.has_key(constants.LOCATION):
        del sessionDict[constants.LOCATION]
    Configuration.trim()
    Configuration.scope({constants.IP : sessionDict[constants.IP],
                         constants.PORT: sessionDict[constants.PORT]})
    #Configuration.saveMash()

########################################################################
# $Log: protocol.py,v $
# Revision 1.3  2001/09/04 19:12:57  smulloni
# integrated scopeable package into SkunkWeb.
#
# Revision 1.2  2001/08/28 11:38:47  drew_csillag
# now uses normheader
#
# Revision 1.1.1.1  2001/08/05 14:59:58  drew_csillag
# take 2 of import
#
#
# Revision 1.7  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.6  2001/05/04 20:04:40  smullyan
# fix: sessionHandler needed to use SkunkWeb.constants;
# fix: web.protocol (which no longer has a protocol in it, oy!) now
# cleans up a little more carefully and no longer deletes the connection
# object from sessionDict (I may recycle it)
#
# Revision 1.5  2001/05/04 18:38:52  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.4  2001/05/03 17:26:12  smullyan
# added an IP pseudo-directive to SkunkWeb.ConfigAdditives; Host now matches
# strictly (perhaps it should be a glob); port and ip are now put in
# sessionDict by requestHandler; HTTPConnection's "host" field is now the host
# header, if any, with the port removed.
#
# Revision 1.3  2001/05/03 16:14:58  smullyan
# modifications for scoping.
#
# Revision 1.2  2001/05/01 23:03:39  smullyan
# added support for name-based virtual hosts.
#
# Revision 1.1  2001/04/25 20:18:53  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.14  2001/04/23 22:53:55  smullyan
# added support for keep-alive.  Fixed server name (I had left out "SkunkWeb"
# and only included the version).
#
# Revision 1.13  2001/04/23 21:44:29  smullyan
# support for "headersOnly" methods and response statuses in web_experimental;
# mod_skunkweb also now respects its headers_only flag.
#
# Revision 1.12  2001/04/23 04:55:48  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.11  2001/04/20 21:49:53  smullyan
# first working version of http server, still more rough than diamond.
#
# Revision 1.10  2001/04/18 22:46:26  smullyan
# first gropings towards a web server.
#
# Revision 1.9  2001/04/16 17:53:01  smullyan
# some long lines split; bug in Server.py fixed (reference to deleted
# Configuration module on reload); logging of multiline messages can now
# configurably have or not have a log stamp on every line.
#
# Revision 1.8  2001/04/10 22:48:29  smullyan
# some reorganization of the installation, affecting various
# makefiles/configure targets; modifications to debug system.
# There were numerous changes, and this is still quite unstable!
#
# Revision 1.7  2001/04/04 18:11:36  smullyan
# KeyedHooks now take glob as keys.  They are tested against job names with
# fnmatch.fnmatchcase.   The use of '?' is permitted, but discouraged (it is
# also pointless).  '*' is your friend.
#
# Revision 1.6  2001/04/04 14:46:31  smullyan
# moved KeyedHook into SkunkWeb.Hooks, and modified services to use it.
#
# Revision 1.5  2001/04/02 22:31:42  smullyan
# bug fixes.
#
# Revision 1.4  2001/04/02 15:06:39  smullyan
# fixed some typos.
#
# Revision 1.3  2001/04/02 00:02:54  smullyan
# integration of new hook framework (in requestHandler.hooks) into
# web_experimental and templating_experimental services.
#
