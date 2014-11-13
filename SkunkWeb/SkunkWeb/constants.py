#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <01/05/04 13:31:34 smulloni>
########################################################################

"""
a repository for constants defined by other services.
"""

# Keys in the requestHandler session dictionary.
# Dependent services will add more here.

IP='ip'
PORT='port'
SERVER_PORT='server_port'
UNIXPATH='unixpath'
JOB='job'
CONNECTION='connection'
HOST='host'
LOCATION='location'

HTTP_VERSION='httpVersion'
CONNECTION_CLOSE='connectionClose'

# Job names for standard services.

WEB_JOB="/web/"
AE_COMPONENT_JOB='/ae_component/'
REMOTE_JOB=AE_COMPONENT_JOB + "/remote/"
TEMPLATING_JOB= WEB_JOB + AE_COMPONENT_JOB + '/templating/'
CGI_JOB = WEB_JOB + '/cgi/'
PYCGI_JOB = WEB_JOB + '/pycgi/'
########################################################################
# $Log: constants.py,v $
# Revision 1.6  2003/05/01 20:45:56  drew_csillag
# Changed license text
#
# Revision 1.5  2002/09/30 20:02:27  smulloni
# support for scoping based on SERVER_PORT.
#
# Revision 1.4  2002/07/24 01:57:57  smulloni
# experimental, not to be much recommended pycgi service.
#
# Revision 1.3  2002/07/11 19:21:55  drew_csillag
# added CGI_JOB
#
# Revision 1.2  2001/10/02 00:06:35  smulloni
# fixes for unix sockets, which were broken due to profound cognitive
# impairment.
#
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
# Revision 1.2  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.1  2001/05/04 18:38:53  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
########################################################################
