#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 13:27:45 smulloni>
########################################################################

import SkunkWeb.ServiceRegistry
SkunkWeb.ServiceRegistry.registerService("httpd")


from SkunkWeb import Configuration, Hooks
from socket import getfqdn as _getfqdn
Configuration.mergeDefaults(lookupHTTPRemoteHost=0,
                            HTTPKeepAliveTimeout=0,
                            HTTPListenPorts=['TCP::8080'],
                            ServerName=_getfqdn())

class _hooker:
    def __init__(self, handler, adder, ports):
        self.adder=adder
        self.handler=handler
        self.ports=ports

    def __call__(self, *a, **kw):
        self.adder(self.handler, self.ports)
    
if Configuration.HTTPListenPorts:
    import requestHandler.requestHandler as rh
    import protocol as prot
    httpProt=prot.HTTPProtocol()

    httpProt.addHandlers(prot.DisembodiedHandler("GET"),
                         prot.DisembodiedHandler("HEAD"),
                         prot.PotentiallyBodaciousHandler("POST"))
    Hooks.ServerStart.append(_hooker(httpProt,
                                     rh.addRequestHandler,
                                     Configuration.HTTPListenPorts))
    

########################################################################
# $Log: __init__.py,v $
# Revision 1.5  2004/03/01 16:27:04  smulloni
# changing default value of HTTPKeepaliveTimeout to zero, as the previous default
# was very irritating if you tried to use siege or apache bench against httpd
#
# Revision 1.4  2003/05/01 20:45:53  drew_csillag
# Changed license text
#
# Revision 1.3  2002/05/24 20:56:20  smulloni
# now add request handlers in ServerStart hook
#
# Revision 1.2  2001/09/07 16:40:44  smulloni
# improved handling of SERVER_NAME
#
# Revision 1.1.1.1  2001/08/05 15:00:01  drew_csillag
# take 2 of import
#
#
# Revision 1.6  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.5  2001/05/04 18:38:48  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.4  2001/04/25 20:18:44  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.3  2001/04/20 21:49:52  smullyan
# first working version of http server, still more rough than diamond.
#
# Revision 1.2  2001/04/19 21:44:55  smullyan
# added some detail to sw.conf.in; added SKUNKWEB_SERVER_VERSION variable to
# SkunkWeb package; more preliminary work on httpd service.
#
# Revision 1.1  2001/04/18 22:46:25  smullyan
# first gropings towards a web server.
#
########################################################################
