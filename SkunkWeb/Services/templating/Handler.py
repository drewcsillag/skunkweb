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
#$Id: Handler.py,v 1.11 2001/07/29 15:44:54 drew Exp $

import AE.Cache
import AE.Component
import AE.MimeTypes
import AE.Error
import AE.Executables
from SkunkWeb import Configuration
import stat
from SkunkWeb.LogObj import ERROR, DEBUG
from web.protocol import Redirect
from SkunkWeb.ServiceRegistry import TEMPLATING

Configuration.mergeDefaults(
    indexDocuments = ['index.html'],
    hideMimeTypes = [
        "text/x-stml-component",
        "text/x-stml-python-component",
        "text/x-stml-data-component",
        "text/x-stml-python-data-component",
        ],
    interpretMimeTypes = [
        "text/html",
        "application/x-python"
        ]
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

def _pathSlashRedirect(connObj, uri):
    connObj.responseHeaders['Location'] = (
        "http://%s%s/" % (connObj.requestHeaders['Host'], uri))
    connObj.setStatus(301) # redirect
    return connObj.response()

def requestHandler(connObj, sessionDict):
    uri = connObj.uri

    try:
        DEBUG(TEMPLATING, "statting %s" % uri)
        st = AE.Cache._statDocRoot(uri)
        connObj.statInfo = st
    except:
        return
    
    if stat.S_ISDIR(st[stat.ST_MODE]): # if a directory fix uri as appropriate
        DEBUG(TEMPLATING, "%s is a directory" % uri)
        if uri[-1] != '/':
            DEBUG(TEMPLATING, "doesn't end in / redirecting")
            return _pathSlashRedirect(connObj, uri)
        else:
            DEBUG(TEMPLATING, "looping over indexDocuments")
            for i in Configuration.indexDocuments:
                s = "%s%s" % (uri, i)
                DEBUG(TEMPLATING, "trying %s" % i)
                try:
                    st = None
                    st = AE.Cache._statDocRoot(s)
                except:
                    DEBUG(TEMPLATING, "nope")
                else:
                    DEBUG(TEMPLATING, "Bingo!")
                    connObj.statInfo = st
                    break
            if not st: #no index document exists
                return
            connObj.uri = s
            DEBUG(TEMPLATING, "uri is now %s" % s)

    connObj.mimeType = mimeType = AE.MimeTypes.getMimeType(connObj.uri)
    DEBUG(TEMPLATING, 'mime type is %s' % mimeType)
    
    #if not a template, don't handle
    #if mimeType not in Configuration.templateMimeTypes:
    if (not AE.Executables.executableByTypes.has_key(
        (mimeType, AE.Executables.DT_REGULAR))
        or mimeType in Configuration.hideMimeTypes):
        DEBUG(TEMPLATING, "not a template or hidden % s" % mimeType)
        return

    #if a templatable thing, but we've been told not to interpret it but
    #to pass it through, ignore and let the plain handler do it
    if mimeType not in Configuration.interpretMimeTypes:
        return

    modTime = st[stat.ST_MTIME]

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
        return #file doesn't exist, screw it
    if not hasattr(connObj, 'mimeType'):
        return #file exists, but is a directory
    if connObj.mimeType in Configuration.hideMimeTypes:
        return #something that shouldn't be uri accessible
        
    connObj.responseHeaders['Content-Type'] = connObj.mimeType
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
        connObj.write(
"""Sorry the requested document (<tt>%s</tt>) is not available""" % connObj.uri)
    return  connObj.response()
                                                 
