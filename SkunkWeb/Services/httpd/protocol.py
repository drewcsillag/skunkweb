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
# $Id: protocol.py,v 1.3 2001/09/07 16:40:44 smulloni Exp $
# Time-stamp: <01/05/04 13:27:08 smulloni>
########################################################################

from requestHandler.protocol import Protocol, PreemptiveResponse
from aecgi import RequestFailed
from web.protocol import _http_statuses, HaveConnection, HandleConnection
from SkunkWeb.ServiceRegistry import HTTPD
from SkunkWeb.LogObj import DEBUG, ACCESS
from SkunkWeb import Configuration, constants
import exceptions
import re
import urllib
import socket

# the below takes a url and looks for the following nice goodies:
# path (anything before the following)
# params (anything after a semicolon and before a question or hash mark)
# query (anything after a question mark and before a hash mark)
# info (fragment/target: anything after a hash mark)
# Note what this does not do:
# 1. it does not separate off scheme/port if they are present
#    (this is supposed to be given a path, not a URI)
# 2. it does not find extra path info (to do that would involve
#    comparing the stated path with the tree structure it describes)

pathRE=re.compile(r"(?P<path>[^;?#]*)" \
                  r"(?:;(?P<params>[^?#]*))?" \
                  r"(?:\?(?P<query>[^#]*))?" \
                  r"(?:#(?P<info>.*))?")

# key in the sessionDict under the which the current httpVersion is kept
constants.HTTP_VERSION="httpVersion"

# pretty unlikely that anything else will care about this, but
# just in case, as it does go into the sessionDict
constants.CONNECTION_CLOSE='connectionClose'

class BadRequestException(exceptions.Exception): pass

class HTTPMethodRequestParser:
    """
    base class that for method-specific request marshallers,
    responsible for reading in the request and building the
    data structure SkunkWeb expects a cgi-like request to arrive in.
    """
    def __init__(self, methodName):
        self.methodName=methodName

    def parseRequest(self,
                     sock,
                     socketFile,
                     methodName,
                     requestURI,
                     httpVersion):
        """
        depending on the type of request, the handler can do different things.
        for a GET, for instance, no attempt needs to be made to read the request
        body.  Various utility methods are provided for behaviors that different
        methods are expected to share.
        """
        raise NotImplementedError

    def _getHeaders(self, socketFile):
        """
        read all the headers, up until the first line with just a CRLF.
        """
        raw_headers=[]
        while 1:
            header=socketFile.readline()
            if not header:
                raise BadRequestException, "premature end of request headers"
            elif header=='\r\n' or header=='\n' :
                break
            else:
                raw_headers.append(header)
        return _getHeaderDict(raw_headers)

    def _getContentLengthDelimitedRequestBody(self, socketFile, headers):
        """
        reads the request body for the case where a content-length
        is declared in the request-headers.  Does not handle chunked
        encoding or multipart/byteranges.
        """
        if not headers.has_key("Content-Length"):
            DEBUG(HTTPD, "no content length in headers")
            return -1
        try:
            contentLength=int(headers['Content-Length'])
        except ValueError:
            DEBUG(HTTPD, "content-length cannot be parsed: %s"
                  % headers['Content-Length'])
            return -1
        return socketFile.read(contentLength)

    def _getChunkedRequestBody(self, socketFile, headers):
        
        #  (quote from RFC 2068, section 19.4.6)
        
        # A process for decoding the "chunked" transfer coding (section 3.6)
        # can be represented in pseudo-code as:
        #        
        # length := 0
        # read chunk-size, chunk-ext (if any) and CRLF
        # while (chunk-size > 0) {
        #       read chunk-data and CRLF
        #       append chunk-data to entity-body
        #       length := length + chunk-size
        #       read chunk-size and CRLF
        # }
        # read entity-header
        # while (entity-header not empty) {
        #       append entity-header to existing header fields
        #       read entity-header
        # }
        # Content-Length := length
        # Remove "chunked" from Transfer-Encoding
        
        # (end quote)
        
        length=0
        entity_body=''
        entity_headers=[]
        chunk_sizeStr, chunk_ext=socketFile.readline().split(";", 2)
        chunk_sizeStr=chunk_sizeStr.strip()
        if chunk_sizeStr.isdigit():
            chunk_size=int(chunk_sizeStr, 16)
        else:
            DEBUG(HTTPD, "invalid chunk size: %s" % chunk_sizeStr)
            return -1
        while chunk_size>0:
            chunk_data=socketFile.read(chunk_size)
            entity_body+=chunk_data
            length+=chunk_size
            # read CRLF
            if socketFile.read(2)!="\r\n":
                DEBUG(HTTPD, "invalid chunk size -- expected CRLF")
                return -1
            chunk_size=int(socketFile.readline().strip(), 16)
        line=socketFile.readline()
        while line.strip():
            entity_headers.append(line)
        # now munge headers
        if len(entity_headers):
            headers.extend(_getHeaderDict(entity_headers))
        return entity_body

# It isn't clear to me that I would ever get one of these, although I might send them.
##    def _getMultipartByteRangesRequestBody(self, socketFile, headers):
##        # TO BE DO
##        return -1

    def _getEnv(self,
                sock,
                methodName,
                requestURI,
                httpVersion,
                headers): 
        
        # parse the requestURI
        match=pathRE.match(urllib.unquote(requestURI))                        
        peeraddress, peerport=sock.getpeername()
        
        env={ 'GATEWAY_INTERFACE': 'CGI/1.1',
              # possibly the following should come from somewhere else
              'SERVER_NAME' : Configuration.ServerName,
              # the current server version
              'SERVER_SOFTWARE' : 'SkunkWeb %s' % Configuration.SkunkWebVersion,
              # this protocol version that called the script
              'SERVER_PROTOCOL': httpVersion, 
              'SERVER_PORT' : sock.getsockname()[1],
              'REQUEST_METHOD': methodName,
              # ??? what to do here? SkunkWeb/Apache is wrong here
              #'PATH_INFO' : '',
              # ??? and here? same deal
              #'PATH_TRANSLATED' : '',            
              # the following I won't add; an authorization service can do so
              # (basicauth does)
              #'REMOTE_USER' : '', 
              #'AUTH_TYPE' : '',
              # this may need to be fudged later too
              # (for index documents, for instance)
              'SCRIPT_NAME' : match.group('path'), 
              'QUERY_STRING' : match.group('query') or '',
              'REMOTE_ADDR' : peeraddress,
              'REMOTE_PORT' : peerport }
        
        # the following, as it involves a potentially expensive DNS lookup,
        # is optional.
        if Configuration.lookupHTTPRemoteHost:
            env['REMOTE_HOST']= socket.gethostbyaddr(peeraddress)
            
        # put in conventional values that duplicate info in headers
        for k1, k2 in (('Content-Type', 'CONTENT_TYPE'),
                       ('Content-Length', 'CONTENT_LENGTH'),
                       ('Accept', 'HTTP_ACCEPT'),
                       ('Accept-Encoding', 'HTTP_ACCEPT_ENCODING'),
                       ('Accept-Language', 'HTTP_ACCEPT_LANGUAGE'),
                       ('User-Agent', 'HTTP_USER_AGENT'),
                       ('Cookie', 'HTTP_COOKIE')):
            if headers.has_key(k1):
                env[k2]=headers[k1]
        return env


class DisembodiedHandler(HTTPMethodRequestParser):
    """
    an HTTPMethodRequestParser for methods where no request body is permitted
    or expected: GET, HEAD, DELETE, OPTIONS, etc.
    """
    def marshalRequest(self,
                       sock,
                       socketFile,
                       methodName,
                       requestURI,
                       httpVersion):
        headers=self._getHeaders(socketFile)
        env=self._getEnv(sock,
                        methodName,
                        requestURI,
                        httpVersion,
                        headers)
        return {'environ': env,
                'headers': headers,
                'stdin'  : ''}

class PotentiallyBodaciousHandler(HTTPMethodRequestParser):
    """
    an HTTPMethodRequestParser for methods that may or may not have a request
    body.  If a content-length and chunked transfer-encoding are both present, the
    content-length is ignored, as per RFC 2068 section 4.4.
    """
    def marshalRequest(self,
                       sock,
                       socketFile,
                       methodName,
                       requestURI,
                       httpVersion):
        headers=self._getHeaders(socketFile)
        stdin=''
        if headers.get('Transfer-Encoding', '').lower()=='chunked':
            stdin=self._getChunkedRequestBody(socketFile, headers)
        elif headers.get('Content-Length', 0)>0:
            stdin=self._getContentLengthDelimitedRequestBody(socketFile,
                                                             headers)

        else:
            page=preemptive_http_error(httpVersion, 501, "Not Implemented")
            raise PreemptiveResponse, page
        env=self._getEnv(sock,
                        methodName,
                        requestURI,
                        httpVersion,
                        headers)
        return {'environ': env,
                'headers': headers,
                'stdin'  : stdin}

# a hook for HaveConnection that plants a flag in the sessionDict
# for the terminateSession() method of HTTPProtocol to read and
# obey.
def _seekTerminus(conn, sessionDict):
    httpVersion=sessionDict.get(constants.HTTP_VERSION, '')
    connHeader=conn.requestHeaders.get('Connection', '')
    if httpVersion=='HTTP/1.0':            
        close = connHeader!='Keep-Alive'        
    elif httpVersion=='HTTP/1.1':
        close = connHeader=='Close'            
    else:
        close=1
    if close:
        conn.responseHeaders['Connection']='Close'
    sessionDict[constants.CONNECTION_CLOSE]=close
    DEBUG(HTTPD, "setting connectionClose flag: %d" % close)

def _healHeaders(raw):
    """
    headers are allowed to continue on to the next line
    if the next line begins with a space or tab.
    This joins them back together.
    """
    joined=[]
    for h in raw:
        if h[0].isspace() and len(joined) and len(h)>1:
            joined[-1]+=h[1:]
        else:
            joined.append(h)
    return joined

#def _fixHeaderName(name):
#    return '-'.join([x.capitalize() for x in name.split('-')])
import skunklib
_fixHeaderName=skunklib.normheader

def _getHeaderDict(headerLines):
    headers={}
    DEBUG(HTTPD, "headerLines: %s" % headerLines)
    DEBUG(HTTPD, "healed: %s" % _healHeaders(headerLines))
    for h in _healHeaders(headerLines):

        name, value=map(lambda x: x.strip(), h.split(":", 1))
        # for convenience, convert digits (like content length) to ints
        if value.isdigit():
            value=int(value)
        headers[_fixHeaderName(name)]=value                   
    return headers

def preemptive_http_error(httpVersion, statusCode, message):
    """
    constructs a default error page for the particular status code,
    which must be in the 400 - 599 range.  This could be prettied up
    quite a bit -- should have the server name and goodies like that.
    Replace this method with something fancier if you want.
    """
    page=[("%s %s" % (httpVersion, _getTextForStatus(statusCode))).strip(),
          'Content-Type: text/plain',
          'Content-Length: %d' % len(message),
          '',
          message]
    return "\r\n".join(page)
    
def _getTextForStatus(statusCode):
    if _http_statuses.has_key(statusCode):
        return _http_statuses[statusCode]
    else:
        return "%d Unknown Error" % statusCode

class HTTPProtocol(Protocol):

    statusRE=re.compile(r"Status\: (?P<status>\d\d\d\s.*)")
    
    """
    implements the server side of the HTTP protocol, in order to serve
    web requests directly
    """
##    # job specifier stuff below pasted from AecgiProtocol.
##    # I wonder whether to move this job-specifier code to Protocol,
##    # or to an intermediate subclass. -- js Fri Apr 13 14:11:05 2001
##    def __init__(self, jobSpecifier):
##        self.jobSpecifier=jobSpecifier
##        self.handlers={}

##    def _getJob(self, requestData):
##        if callable(self.jobSpecifier):
##            return apply(self.jobSpecifier, [requestData])
##        else:
##            return self.jobSpecifier
    def __init__(self):
        self.handlers={}
        
    def addHandlers(self, *methodHandlers):
        for mh in methodHandlers:
            self.handlers[mh.methodName]=mh
            
    def marshalRequest(self, sock, sessionDict):
        """
        this reads one non-blank line from the socket and determines the HTTP
        method, then looks for a method handler to handle the rest of the
        marshalling.  If none can be found, raises a PreemptiveResponse with a
        405 error.
        
        -- standard HTTP input format:

        request line
        header lines
        CRLF
        data

        The method handler should produce output in the following format, 
        fit to be consumed by the HTTPConnection object:
        
        a 2-tuple, the first item being a jobname, the second a dictionary with:
            - an 'environ' sub-dictionary (equivalent to what the Apache
              environment would be)
            - a 'stdin' string, the body of the request (if any)
            - a 'headers' sub-dictionary.

        The idea is that the marshalled request here should be
        more or less identical to the same web request filtering through apache
        and aecgi.        
        """
        sockfile=sock.makefile("rb", 0)
        
        # (quote from rfc 2068, section 4.1)
        # In the interest of robustness, servers SHOULD ignore any empty
        # line(s) received where a Request-Line is expected. In other words, if
        # the server is reading the protocol stream at the beginning of a
        #  message and receives a CRLF first, it should ignore the CRLF.
        # (end quote)
        # I will support a more than adequate finite number of CRLFs before the
        # status line, but not loop indefinitely. 
        
        requestLine=sockfile.readline()
        if not requestLine.strip():
            blank=1
            # MAXIMUM NUMBER OF TOLERATED BLANKS = 10
            for cnt in range(10): 
                requestLine=sockfile.readline()
                if requestLine.strip():
                    blank=0
                    break
            if blank:
                # what is the appropriate error?
                # XXX
                sockfile.close()
                page=preemptive_http_error("",
                                           400,
                                           "The request could not be parsed: " \
                                           "request line not found.")
                raise PreemptiveResponse, page
            
        # we have a Request-Line.  It must be of the form:
        # (quote from rfc 2068, section 5.1)
        # Request-Line   = Method SP Request-URI SP HTTP-Version CRLF
        # (end quote)
        # However, HTTP 0.9 clients won't send an HTTP-Version,
        # and I'll accomodate them.

        # no alternate forms of whitespace allowed!
        tokenTuple=map(lambda x: x.strip(), requestLine.split(' '))
        if len(tokenTuple)==3:
            method, requestURI, httpVersion=tokenTuple
        elif len(tokenTuple)==2:
            method, requestURI=tokenTuple
            httpVersion='' # 0.9 style request.  Not fully supported.
        else:
            sockfile.close()
            page=preemptive_http_error("",
                                       400,
                                       "The request could not be parsed: "\
                                       "request line \n\n\t\"%s\"\n\n has"\
                                       "wrong number of tokens" % requestLine)
            raise PreemptiveResponse, page
        handler=self.handlers.get(method, None)
        if not handler:
            sockfile.close()
            page=preemptive_http_error(httpVersion,
                                      405,
                                      "No handler for method %s" % method)
            raise PreemptiveResponse, page
        # check httpVersion.  We support 1.0 and 1.1.
        sessionDict[constants.HTTP_VERSION]=httpVersion
        requestData=handler.marshalRequest(sock,
                                           sockfile,
                                           method,
                                           requestURI,
                                           httpVersion)

        sockfile.close()
        #return (self._getJob(requestData), requestData)
        return requestData

    def marshalResponse(self, response, sessionDict):

        # the status header needs to be pulled out of the
        # response and  stuck in the http status line.
        # how about a more efficient way of doing this? IMPROVE ME
        httpVersion=sessionDict.get(constants.HTTP_VERSION, '')
        statusLine='%s %s\r\n'
        status='200 OK'
        lines=[]
        newRes=''
        reslen=0
        DEBUG(HTTPD, "in marshalResponse with response %s" % response)
        
        if response==None:
            response=''
        for line in response.split('\r\n'):
            reslen+=2+len(line)
            if line=='':
                newRes+='\r\n'+response[reslen:]
                break
            else:
                match=HTTPProtocol.statusRE.match(line)
                if match:
                    status=match.group('status')
                    DEBUG(HTTPD, "found status: \"%s\"" % status)                    
                else:                   
                    newRes+=line+'\r\n' 
                
        completeResponse=(statusLine % (httpVersion, status)).lstrip() + newRes
        DEBUG(HTTPD, "complete response is %s" % completeResponse)
        return completeResponse

    def marshalException(self, exc_text, sessionDict):
        res=RequestFailed(constants.WEB_JOB, exc_text, sessionDict)
        if res:
            return res
        else:
            # dummy up a 500. 
            httpVersion=sessionDict.get(constants.HTTP_VERSION, '')
            return '\r\n'.join([('%s 500 Internal Server Error' % httpVersion).strip(),
                                'Content-Type: text/plain',
                                'Content-Length: %d' % len(exc_text),
                                '',
                                exc_text])

    def keepAliveTimeout(self, sessionDict):
        if sessionDict.get(constants.CONNECTION_CLOSE, 1):
            return -1
        else:
            return Configuration.HTTPKeepAliveTimeout

jobGlob=constants.WEB_JOB+'*'
HaveConnection.addFunction(_seekTerminus, jobGlob)

########################################################################
# $Log: protocol.py,v $
# Revision 1.3  2001/09/07 16:40:44  smulloni
# improved handling of SERVER_NAME
#
# Revision 1.2  2001/08/28 11:38:47  drew_csillag
# now uses normheader
#
# Revision 1.1.1.1  2001/08/05 15:00:01  drew_csillag
# take 2 of import
#
#
# Revision 1.12  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.11  2001/05/04 18:38:48  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.10  2001/04/25 20:18:45  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.9  2001/04/24 21:43:02  smullyan
# fixed bug in httpd.protocol (was accidentally removing line return after
# HTTP response line, producing weirdness).  Removed call of deprecated
# method of config object in remote.__init__.py; added list of configuration
# variables that need to be documented to sw.conf.in.
#
# Revision 1.8  2001/04/23 22:53:54  smullyan
# added support for keep-alive.  Fixed server name (I had left out "SkunkWeb"
# and only included the version).
#
# Revision 1.7  2001/04/23 20:17:16  smullyan
# removed SKUNKWEB_SERVER_VERSION, which I found was redundant; fixed typo in
# httpd/protocol; renamed "debugServices" configuration variable to
# "initialDebugServices".
#
# Revision 1.6  2001/04/23 18:52:55  smullyan
# basicauth repaired.
#
# Revision 1.5  2001/04/23 17:30:07  smullyan
# basic fixes to basic auth and httpd; added KeepAliveTimeout to requestHandler,
# using select().
#
# Revision 1.4  2001/04/23 04:55:43  smullyan
# cleaned up some older code to use the requestHandler framework; modified
# all hooks and Protocol methods to take a session dictionary argument;
# added script to find long lines to util.
#
# Revision 1.3  2001/04/20 21:49:52  smullyan
# first working version of http server, still more rough than diamond.
#
# Revision 1.2  2001/04/19 21:44:56  smullyan
# added some detail to sw.conf.in; added SKUNKWEB_SERVER_VERSION variable to
# SkunkWeb package; more preliminary work on httpd service.
#
# Revision 1.1  2001/04/18 22:46:25  smullyan
# first gropings towards a web server.
#
########################################################################
