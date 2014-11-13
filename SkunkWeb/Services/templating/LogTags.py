#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
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
# Revision 1.2  2003/05/01 20:45:54  drew_csillag
# Changed license text
#
# Revision 1.1.1.1  2001/08/05 15:00:07  drew_csillag
# take 2 of import
#
#
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
