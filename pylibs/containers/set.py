######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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

    


