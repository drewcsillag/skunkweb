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
"""
For now, just contain the sendmail tag
"""
# $Id: SendmailTag.py,v 1.1.1.1 2001/08/05 15:00:07 drew_csillag Exp $

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
