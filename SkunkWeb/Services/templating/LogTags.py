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
# $Id: LogTags.py,v 1.3 2001/07/09 20:38:40 drew Exp $
# Time-stamp: <01/04/12 12:52:32 smulloni>
########################################################################

"""
Log tags - various tags which implement user level logging.
"""


from AE.CommonStuff import *

from SkunkWeb import LogObj, ServiceRegistry

class GenericLogTag(DTTag):
    """the <:log:>, <:debug:>, <:warn:>, and <:error:> tags"""
    def __init__(self, name, function):
        DTTag.__init__ ( self, name, isempty=1, modules = [LogObj, ServiceRegistry])
        self._func = function

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)

        args = DTUtil.tagCall ( tag, ['msg',] )

        args = DTCompilerUtil.pyifyArgs (tag, args )

        msg = DTCompilerUtil.getTempName()

        codeout.write ( indent, '%s = str(%s)' % (msg, args['msg']) )

        # Just call the appropriate Logger function
        if self._func == 'DEBUG':
            codeout.write ( indent, '__h.LogObj.%s ( __h.ServiceRegistry.USER, %s )' %
                            ( self._func, msg ))
        else:
            codeout.write ( indent, '__h.LogObj.%s ( %s )' %( self._func, msg ))

        codeout.write ( indent, 'del %s' % msg )

#
# Create the list of tags we're exposing
#
LoggingTags = [ GenericLogTag ( 'log', 'LOG' ),
                GenericLogTag ( 'warn', 'WARN' ),
                GenericLogTag ( 'error', 'ERROR' ),
                GenericLogTag ( 'debug', 'DEBUG' ),
              ]

########################################################################
# $Log: LogTags.py,v $
# Revision 1.3  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.2  2001/04/25 20:18:48  smullyan
# moved the "experimental" services (web_experimental and
# templating_experimental) back to web and templating.
#
# Revision 1.2  2001/04/12 17:52:02  smullyan
# brought LogTags into sync with changes to debug system.
#
########################################################################
