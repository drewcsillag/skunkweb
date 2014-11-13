########################################################################
# Time-stamp: <2006-04-21 16:51:39 smulloni>
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

from SkunkExcept import SkunkCriticalError
from SkunkWeb.LogObj import DEBUG, HTTP_ACCESS, logException
from SkunkWeb.ServiceRegistry import WEB
from SkunkWeb import Configuration, ConfigAdditives, constants
from requestHandler.protocol import Protocol, PreemptiveResponse
from skunk.date.format import HTTPDate
import Cookie
import SocketScience
import cStringIO
import cgi
import marshal
import sys
import time
import types
import browser
from SkunkWeb.Hooks import KeyedHook, Hook
import argextract
import base64
import md5
try:
    import gzip
except:
    pass
import re
rangere = re.compile(r'bytes=([0-9]*)-([0-9]*)$')

Configuration.mergeDefaults(
    textCompression=0,
    generateEtagHeader=1,
    )
headersOnlyMethods=['HEAD'] 
headersOnlyStatuses=[100, 101, 102, 204, 304]

HaveConnection=KeyedHook()
PreHandleConnection=KeyedHook()
RouteConnection=KeyedHook()
HandleConnection=KeyedHook()
ProcessResponse=Hook()

class HTTPConnection:
    '''
    The connection object used for HTTP, passed to various web hooks.
    '''
    def __init__(self, requestData):
        self._output=cStringIO.StringIO()
        self.env = requestData['environ']
        self._requestDict=requestData
        self._status=200
        self._rawOutput=''
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
        stdin = cStringIO.StringIO(requestData['stdin'])
        env = requestData['environ']
        try:
            query = cgi.FieldStorage(fp = stdin, environ = env,
                                     keep_blank_values = 1)
            self.args=self._convertArgs(query)
            ok=1
        except:
            # may be some exotic content-type
            logException()
            DEBUG(WEB, "content-type: %s" % self.requestHeaders.get("content-type"))
            self.args={}
            ok=0

        if ok and Configuration.mergeQueryStringWithPostData and \
               env.get("REQUEST_METHOD")=='POST':
            #if POST, see if any GET args too
            environ = env.copy()
            environ["REQUEST_METHOD"] = 'GET'            
            query = cgi.FieldStorage(fp = stdin, environ = environ,
                                     keep_blank_values = 1)
            self.args.update(self._convertArgs(query))
        
    def _convertArgs(self, query):
        d = {}
        if query!=None:
            try:
                keys=query.keys()
            except TypeError:
                # annoyingly thrown by cgi.py in some circumstances
                DEBUG(WEB, "TypeError thrown in _convertArgs for query %s" % query)
                return d
            for k in keys:
                d[k] = self._convertArg(query[k])
        return d

    def _convertArg(self, val):
        if type(val) in (types.ListType, types.TupleType):
            return map(self._convertArg, val)
        if val.filename:
            return _File(val)
        return val.value

    def extract_args(self, *args, **kwargs):
        
        """
        extracts and returns a dictionary of the specified fields
        from self.args.  args are argument names to look for; they
        will be placed in the dictionary unconverted, or None if not
        found.  The values for kwargs may be one of three forms:
        
          1. a default value (which must not be a sequence and not callable);
          2. a callable object, which will be taken to be a conversion function;
          3. a sequence of length one or two, the first item of which must
             be a callable and will be used as a conversion function, and the
             second item of which, if present, will be used as a default value.

        This is supposed to be equivalent to the <:args:> tag in STML.
        """
        return argextract.extract_args(self.args, *args, **kwargs)

    def _initHeaders(self):
        self.requestHeaders = HeaderDict(self._requestDict['headers'])
        self.responseHeaders = HeaderDict({
            #'Server': 'SkunkWeb %s' % Configuration.SkunkWebVersion,
            'Date': str(HTTPDate()),
            'Status': '200 OK'
            })

    def _initCookies(self):
        self.requestCookie = Cookie.SimpleCookie()
        if self.requestHeaders.has_key('Cookie'):
            try:
                self.requestCookie.load(self.requestHeaders['Cookie'])
            except Cookie.CookieError:
                logException()
        self.responseCookie = Cookie.SimpleCookie()        

    def _initURI(self, env):
        self.uri=self.realUri = env.get('SCRIPT_NAME', '') + env.get('PATH_INFO', '')

    def setContentType(self, type):
        self.responseHeaders['Content-Type'] = type
        
    def response(self):
        rawOutput = self._output.getvalue()
        headers = ''
        
        if Configuration.textCompression:
            ae = self.requestHeaders.get('accept-encoding', '').split(',')
            for i in ('gzip', 'x-gzip'):
                if (i in ae
                    and str(self.responseHeaders.get('content-type'))[:5] == 'text/'):
                    rawOutput = _compressit(rawOutput)
                    self.responseHeaders['Content-Encoding'] = i
                    break

        if Configuration.generateEtagHeader:
            etagval = base64.encodestring(md5.new(rawOutput).digest())[:-1]
            self.responseHeaders['etag'] = etagval

        rnghdr = self.requestHeaders.get('range')
        if rnghdr:
            match = rangere.search(rnghdr)
            if match:
                st, en = match.groups()
                lro = len(rawOutput)
                if st and en:
                    rawOutput = rawOutput[int(st):int(en)+1]
                    rst = int(st)
                    ren = int(en)
                elif st:
                    rawOutput = rawOutput[int(st):]
                    rst = int(st)
                    ren = lro - 1
                else:
                    rawOutput = rawOutput[-int(en):]
                    rst = lro - int(en)
                    ren = lro - 1
                self.responseHeaders['Content-Range']='bytes %d-%d/%d' % (
                    rst, ren, lro)
        # store the raw output (for logging purposes)
        self._rawOutput=rawOutput
        if not self.responseHeaders.has_key('Content-Length'):
            self.responseHeaders['Content-Length'] = len(rawOutput)
        if self.responseCookie.keys():
            headers = headers + str(self.responseCookie) + '\r\n'
        for i in self.responseHeaders.items():
            headers = headers + "%s: %s\r\n" % i
        if self.method in headersOnlyMethods or self._status in headersOnlyStatuses:
            return headers+"\r\n"
        else:
            return "%s\r\n%s" % (headers, rawOutput)
    
    def setStatus(self, status):
        try:
            self.responseHeaders['Status'] = _http_statuses[status]
        except KeyError:
            raise SkunkCriticalError, 'invalid status: %s' % status
        self._status = status
        
    def redirect(self, url, status=301):
        if status not in (301, 302):
            raise ValueError, "invalid status for redirect: %s" % status
        self.responseHeaders['Location'] = url
        self.setStatus(status)
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
        return self._d.get(self._fixHeader(k), default)

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
    
    # DEBUG(WEB, 'creating Connection')
    # DEBUG(WEB, 'requestData is %s' % str(requestData))
    connection=HTTPConnection(requestData)

    sessionDict[constants.CONNECTION]=connection
    sessionDict[constants.HOST]=connection.host
    sessionDict[constants.LOCATION]=connection.uri
    sessionDict[constants.SERVER_PORT]=int(connection.env['SERVER_PORT'])
    try:
        # DEBUG(WEB, 'executing HaveConnection hook')
        HaveConnection(Configuration.job, connection, sessionDict)
        # DEBUG(WEB, 'survived HaveConnection hook')

        # overlay of config information
        Configuration.trim()
        Configuration.scope(sessionDict)
        #Configuration.saveMash()

        # DEBUG(WEB, 'executing PreHandleConnection hook')
        PreHandleConnection(Configuration.job, connection, sessionDict)
                
    except PreemptiveResponse, pr:
        # DEBUG(WEB, 'got preemptive response')
        response=pr.responseData
    except:
        logException()
    else:
        RouteConnection(Configuration.job, connection, sessionDict)
        # DEBUG(WEB, 'handling connection')
        response=HandleConnection(Configuration.job, connection, sessionDict)

    # so the response can be further processed, add it to the sessionDict temporarily
    sessionDict['RESPONSE']=response
    ProcessResponse(connection, sessionDict)
    response=sessionDict['RESPONSE']
    del sessionDict['RESPONSE']
    
    # the connection should be available to postResponse and cleanup hooks.
    sessionDict[constants.CONNECTION]=connection
    # DEBUG(WEB, 'returning response: %s' % response)
    #if response!=None:
    #    DEBUG(WEB, 'length of response: %d' % len(response))
    return response


def _cleanupConfig(requestData, sessionDict):
    """
    function for requestHandler's CleanupRequest hook
    """
    if sessionDict.has_key(constants.HOST):
        del sessionDict[constants.HOST]
    if sessionDict.has_key(constants.LOCATION):
        del sessionDict[constants.LOCATION]
    if sessionDict.has_key(constants.SERVER_PORT):
        del sessionDict[constants.SERVER_PORT]
    Configuration.trim()

    if sessionDict.has_key(constants.IP):
        Configuration.scope({constants.IP : sessionDict[constants.IP],
                             constants.PORT: sessionDict[constants.PORT]})
    elif sessionDict.has_key(constants.UNIXPATH):
        Configuration.scope({constants.UNIXPATH : sessionDict[constants.UNIXPATH]})
    #Configuration.saveMash()

def _compressit(txt):
    # have to screw with time so it doesn't wind up in the gzipped thing
    oldtime = time.time
    time.time = lambda x=0:0
    outt = cStringIO.StringIO()
    outf = gzip.GzipFile(fileobj=outt, mode='wb')
    outf.write(txt)
    outf.close()
    retval = outt.getvalue()
    time.time=oldtime
    return retval
    
def _accesslog(requestData, sessionDict):
    if Configuration.HttpLoggingOn:
        conn=sessionDict.get(constants.CONNECTION)
        if conn:
            # very tolerant of env being screwed up
            HTTP_ACCESS(remote=conn.env.get('REMOTE_ADDR', '-'),
                        request="%s %s %s" % (conn.method,
                                              conn.uri,
                                              conn.env.get('SERVER_PROTOCOL', '-')),
                        status=conn._status,
                        length=len(conn._rawOutput),
                        auth_user=conn.env.get('REMOTE_USER', '-'))
    
