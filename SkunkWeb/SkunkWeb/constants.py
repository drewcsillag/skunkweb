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
# $Id: constants.py,v 1.1.1.1 2001/08/05 14:59:37 drew_csillag Exp $
# Time-stamp: <01/05/04 13:31:34 smulloni>
########################################################################

"""
a repository for constants defined by other services.
"""

# Keys in the requestHandler session dictionary.
# Dependent services will add more here.

IP='ip'
PORT='port'
UNIXPATH='unixpath'
JOB='job'
CONNECTION='connection'
HOST='host'
LOCATION='location'

HTTP_VERSION='httpVersion'
CONNECTION_CLOSE='connectionClose'

# Job names.  These shouldn't be  defined here, but
# I haven't figured out a better way, yet -- FIX ME ***

WEB_JOB="/web/"
AE_COMPONENT_JOB='/ae_component/'
REMOTE_JOB=AE_COMPONENT_JOB + "/remote/"
TEMPLATING_JOB= WEB_JOB + AE_COMPONENT_JOB + '/templating/'

########################################################################
# $Log: constants.py,v $
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
