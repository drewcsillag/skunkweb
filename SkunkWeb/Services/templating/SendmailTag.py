#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
For now, just contain the sendmail tag
"""
# $Id: SendmailTag.py,v 1.2 2001/08/14 06:20:43 smulloni Exp $

from AE.CommonStuff import *
import MailServices

class SendmailTag(DTTag):
    """
    Send mail to a list of users
    """
    def __init__(self):
        DTTag.__init__ ( self, 'sendmail', isempty=1, modules=[MailServices])

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, ['to_addrs', 'subject', 'msg', 
                                  ( 'from_addr', None )] )
        args=DTCompilerUtil.pyifyArgs(tag, args)

        # Ok, call the mail function
        codeout.write ( indent, 'if %s:' % args['from_addr'] )
        codeout.write ( indent+4, '__h.MailServices.sendmail ( %s, %s, %s, '
                                  'from_addr = %s )' % ( args['to_addrs'], 
                                  args['subject'], args['msg'], 
                                  args['from_addr'] ) )
        codeout.write ( indent, 'else:' )
        codeout.write ( indent+4, '__h.MailServices.sendmail ( %s, %s, %s )' % 
                                ( args['to_addrs'], args['subject'],
                                  args['msg'], ) )

        # All done
