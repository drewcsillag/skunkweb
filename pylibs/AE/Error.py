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
#$Id: Error.py,v 1.3 2001/07/09 20:38:41 drew Exp $
import cStringIO

import ErrorHandler

import Component
import Executables
import Logs

def logException():
    out = cStringIO.StringIO()
    ErrorHandler.logError(out)
    
    errorTags = [frame.executable.dt._error_tag
                 for frame in Component.componentStack
                 if isinstance(frame.executable, Executables.STMLExecutable)
                 if hasattr(frame.executable.dt, '_error_tag')]
    if errorTags:
        out.write('Tag traceback (most recent tag last):\n')
        for tag in errorTags:
            if tag:
                out.write('  File "%s", line %s\n' % (tag._name, tag._lineno))
                out.write('    %s\n' % tag.tag)
            else:
                out.write('  File ??, line??\n')

    x = out.getvalue()
    Logs.ERROR(x)
    return x

            
