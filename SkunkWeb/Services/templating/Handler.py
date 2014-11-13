# Time-stamp: <2004-01-10 23:04:49 smulloni>

########################################################################
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

import AE.Cache
import AE.Component
import AE.MimeTypes
import AE.Error
import AE.Executables
from SkunkWeb import Configuration
import stat
import sys
from SkunkWeb.LogObj import ACCESS, ERROR, DEBUG
from web.protocol import Redirect
from SkunkWeb.ServiceRegistry import TEMPLATING
import vfs
from skunk.date.format import HTTPDate

Configuration.mergeDefaults(
    indexDocuments = ['index.html'],
    hideMimeTypes = [
        "text/x-stml-component",
        "text/x-stml-python-component",
        "text/x-stml-data-component",
        "text/x-stml-python-data-component",
        "text/x-stml-include",
        "text/x-stml-python-include"
        ],
    interpretMimeTypes = [
        "text/html",
        "application/x-python"
        ],
    defaultIndexHtml = None,
    mimeHandlers = {}
    )

def _handleException(connObj):
    text = AE.Error.logException()
    ERROR(text)
    import cStringIO
    connObj.setStatus(500)
    if (hasattr(Configuration, 'errorTemplate') and
        Configuration.errorTemplate):
        connObj.write(AE.Component.callComponent(
            Configuration.errorTemplate, {'CONNECTION': connObj,
                                          'ERROR_TEXT': text}))
        return connObj.response()
    connObj._output = cStringIO.StringIO(text)
    connObj.responseHeaders['Content-Type'] = 'text/plain'
    return connObj.response()

def _pathSlashRedirect(connObj):
    connObj.responseHeaders['Location'] = (
        "http://%s%s/" % (connObj.requestHeaders['Host'], connObj.realUri))
    connObj.setStatus(301) # redirect
    return connObj.response()

def requestHandler(connObj, sessionDict):
    fixPath=AE.Cache._fixPath
    uri = connObj.uri
    try:
        DEBUG(TEMPLATING, "statting %s" % uri)
        fixed, fs, st=AE.Cache._getPathFSAndMinistat(uri)
        connObj.statInfo = st
    except vfs.VFSException:
        ACCESS("file not found: %s" % uri)
        return
    except:
        return _handleException(connObj)
    
    # if a directory fix uri as appropriate
    if fs.isdir(fixed):
        DEBUG(TEMPLATING, "%s is a directory" % fixed)
        if (not uri) or uri[-1] != '/':
            DEBUG(TEMPLATING, "doesn't end in / redirecting")
            return _pathSlashRedirect(connObj)
        else:
            DEBUG(TEMPLATING, "looping over indexDocuments")
            for i in Configuration.indexDocuments:
                s = "%s%s" % (uri, i)         
                #DEBUG(TEMPLATING, "trying %s" % i)
                fixed=fixPath(Configuration.documentRoot, s)

                try:
                    st = None
                    st = fs.ministat(fixed)
                except:
                    #DEBUG(TEMPLATING, "nope")
                    pass
                else:
                    DEBUG(TEMPLATING, "Bingo!")
                    connObj.statInfo = st
                    break
            if not st: #no index document exists
                if Configuration.defaultIndexHtml:
                    s = Configuration.defaultIndexHtml
                    st = AE.Cache._statDocRoot(uri)
                else:
                    return
            connObj.uri = s
            DEBUG(TEMPLATING, "uri is now %s" % s)

    connObj.mimeType = mimeType = AE.MimeTypes.getMimeType(connObj.uri)
    DEBUG(TEMPLATING, 'mime type is %s' % mimeType)

    # don't handle a hidden mime type
    if mimeType in Configuration.hideMimeTypes:
        DEBUG(TEMPLATING, "hidden mime type: %s" % mimeType)
        return

    if Configuration.mimeHandlers.has_key(mimeType):
        DEBUG(TEMPLATING, "invoking special mime handler for mime type %s" % mimeType)
        return Configuration.mimeHandlers[mimeType](connObj, sessionDict)    
    
    #if not a template, don't handle
    if not AE.Executables.executableByTypes.has_key((mimeType,
                                                     AE.Executables.DT_REGULAR)):
        DEBUG(TEMPLATING, "not a template mime type: %s" % mimeType)
        return

    #if a templatable thing, but we've been told not to interpret it but
    #to pass it through, ignore and let the plain handler do it
    if mimeType not in Configuration.interpretMimeTypes:
        return
    modTime =st[vfs.MST_CTIME]
    if mimeType == 'application/x-python':
        mimeType = 'text/html'

    connObj.responseHeaders['Content-Type'] = mimeType
    try:
        respText = AE.Component.callComponent(
            connObj.uri, {'CONNECTION': connObj},
            srcModTime = modTime)
    except Redirect:
        pass
    except:
        DEBUG(TEMPLATING, "exception occurred rendering component")
        return _handleException(connObj)
    else:
        connObj.write(respText)

    return connObj.response()

def plainHandler(connObj, sessionDict):
    if not hasattr(connObj, 'statInfo'):
        return # file doesn't exist, screw it
    if not hasattr(connObj, 'mimeType'):
        return # file exists, but is a directory
    if connObj.mimeType in Configuration.hideMimeTypes:
        return # something that shouldn't be uri accessible

    modtime = HTTPDate(connObj.statInfo[2])
    ims = connObj.requestHeaders.get('If-Modified-Since')
    if ims:
        if ims == modtime:
            connObj.setStatus(304)
            return connObj.response()
        
    connObj.responseHeaders['Content-Type'] = connObj.mimeType
    connObj.responseHeaders['Last-Modified'] = modtime
    DEBUG(TEMPLATING, "spewing raw file")
    connObj.write(AE.Cache._readDocRoot(connObj.uri))
    return connObj.response()

def fourOhFourHandler(connObj, sessionDict):
    #document not found, or shouldn't be seen
    connObj.setStatus(404)
    connObj.responseHeaders['Content-Type'] = 'text/html'
    if (hasattr(Configuration, 'notFoundTemplate') and
        Configuration.notFoundTemplate):
        connObj.write(AE.Component.callComponent(
            Configuration.notFoundTemplate, {'CONNECTION': connObj}))
    else:
        connObj.write("Sorry the requested document is not available")
    return  connObj.response()
                                                 
