######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
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
########################################################################

class Set(list):
    """
    very simple set implementation. requires Python 2.2+.
    N.B. this is not very efficient; could be made better
    by using a dict rather than relying on 'in'.
    """
    def __setitem__(self, k, v):
        if v not in self:
            list.__setitem(self, k, v)

    def __setslice__(self, i, j, s):
        slice=[x for x in s if x not in self]
        if slice:
            list.__setslice__(self, i, j, slice)
    
    def append(self, item):
        if item not in self:
            list.append(self, item)

    def extend(self, itemlist):
        for item in itemlist:
            self.append(item)

    


