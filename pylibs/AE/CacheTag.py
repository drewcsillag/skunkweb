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
Tag cache - description???
"""
# $Id: CacheTag.py,v 1.2 2001/07/09 20:38:41 drew Exp $

from CommonStuff import *
from DT import DTExcept

# The required modules
from Date import TimeUtil
import time

class CacheTag( DTTag ):
    """the <:cache:> tag"""
    def __init__(self):
        DTTag.__init__ ( self, 'cache', isempty=1,
                         modules = [ TimeUtil, time ] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [('until', 'None'), ('duration', 'None')])
        if args['until'] == 'None' and args['duration']=='None':
            raise DTExcept.DTCompileError ( tag, 
                  'must supply either until or duration argument' )
	args=DTCompilerUtil.pyifyArgs(tag, args)
        tempsecs=DTCompilerUtil.getTempName()
        if args['until'] != None:
            codeout.write(indent, '%s = __h.TimeUtil.convertUntil(%s)'
                          % (tempsecs, args['until']))
        elif args['duration'] != None:
            codeout.write(indent, '%s = __h.TimeUtil.convertDuration(%s)' % 
                          (tempsecs, args['duration']))
        codeout.write(indent, '__expiration = %s' % tempsecs)
        ttupv=DTCompilerUtil.getTempName()
        codeout.write(indent, '%s = __h.time.localtime(%s)' % (ttupv, tempsecs))
        codeout.write(indent, '__h.OUTPUT.write("<!-- cache expires:" + '
                              '__h.time.asctime(%s) + "-->")'  % ttupv)
        codeout.write(indent, 'del %s, %s' % (ttupv, tempsecs))
