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
A collection of helpful utility functions, mostly
for munging data to present in tabular format.
"""

import copy
from types import ListType, TupleType, IntType

def rowmaker(seq, num_columns=2, blank=None):
    """
    Accepts a list or tuple of items seq, and returns
    a list of "slices" from that list/tuple that
    can be used to populate rows of a table with
    num_columns columns in it. The returned list
    contains lists, each of them exactly num_columns
    in length, containing the items of the original list/tuple
    in order. If this function runs out of items in the original
    list/tuple, it uses the object blank, which defaults
    to None, as padding.

    For example, you have a list of numbers
    [0,1,2,3,4,5,6,7,8,9], and you would like 
    to divide them quickly into sets of three items
    each to put in a three-column table, using the 
    empty string ""
    as padding when you run out of items:

    
    >>> from tableutils import rowmaker
    >>> x = [0,1,2,3,4,5,6,7,8,9]
    >>> rows = rowmaker(x, 3, "")
    >>> print rows
    [[0,1,2],[3,4,5],[6,7,8],[9,"",""]]
    >>> for row in rows:
    >>>     print '<TR>'
    >>>     for item in row:
    >>>         print '<TD>%s</TD>' % item
    >>>     print '</TR>'
    <TR>
    <TD>0</TD>
    <TD>1</TD>
    <TD>2</TD>
    </TR>
    <TR>
    <TD>3</TD>
    <TD>4</TD>
    <TD>5</TD>
    </TR>
    <TR>
    <TD>6</TD>
    <TD>7</TD>
    <TD>8</TD>
    </TR>
    <TR>
    <TD>9</TD>
    <TD></TD>
    <TD></TD>
    </TR>
    
    """

    # type/value checking
    if type(seq) not in (ListType, TupleType):
	raise TypeError, "seq argument %s must be list or tuple" % repr(seq)
    if type(num_columns) != IntType:
	raise TypeError, "num_columns argument %s must be integer" % repr(num_columns)
    if num_columns < 1:
        raise ValueError, \
              "num_columns arg %s must be greater than 0" % num_columns

    rows = []
    crow = []
    citems = 0
    for i in seq:
        if citems == num_columns:
            rows.append(crow)
            crow = []
	    citems = 0
        crow.append(i)
	citems = citems + 1
    # if crow is not empty, it needs padding
    if crow:
	for i in range(num_columns - len(crow)):
	    crow.append(blank)
        rows.append(crow)
    return rows

def columnmaker(seq, num_columns=2):
    """
    Given a list or tuple, returns a list of
    num_columns "slices" of the list/tuple,
    divided up as evenly as possible, so that 
    you can display each slice as a column of entries
    in some table.

    If the items in the original list/tuple
    cannot be divided evenly, then the first slice
    or slices will contain one more item than the
    other slices. (See the source code for the
    actual (simple) algorithm.)

    For example, you have a list of numbers
    [0,1,2,3,4,5,6,7,8,9], and you would like 
    to divide them evenly into three lists, each of which
    you will spill into a table column:

    
    >>> from tableutils import columnmaker
    >>> x = [0,1,2,3,4,5,6,7,8,9]
    >>> cols = columnmaker(x, 3)
    >>> print cols
    [[0,1,2,3],[4,5,6],[7,8,9]]
    >>> for col in cols:
    >>>     print '<TD>'
    >>>     print '<UL>'
    >>>     for item in row:
    >>>         print '<LI>%s</LI>' % item
    >>>     print '</UL>'
    >>>     print '</TD>'
    <TD>
    <UL>
    <LI>0</LI>
    <LI>1</LI>
    <LI>2</LI>
    <LI>3</LI>
    </UL>
    </TD>
    <TD>
    <UL>
    <LI>4</LI>
    <LI>5</LI>
    <LI>6</LI>
    </UL>
    </TD>
    <TD>
    <UL>
    <LI>7</LI>
    <LI>8</LI>
    <LI>9</LI>
    </UL>
    </TD>
    
    """

    # type/value checking
    if type(seq) not in (ListType, TupleType):
	raise TypeError, "seq argument %s must be list or tuple" % repr(seq)
    if type(num_columns) != IntType:
	raise TypeError, "num_columns argument %s must be integer" % repr(num_columns)
    if num_columns < 1:
        raise ValueError, \
              "num_columns arg %s must be greater than 0" % num_columns
    l = len(seq)
    lef = l % num_columns
    # algorithm: int(len/num_columns) is the base column length,
    # then starting from leftmost column, add 1 to each column
    # until len items are represented.
    # Notice that a list of "index steps" are used in clens.
    col = int(l / num_columns)
    clens = [col] * num_columns
    lefcount = 0
    for i in range(len(clens)):
        if lefcount == lef: break
        clens[i] = clens[i] + 1
        lefcount = lefcount + 1
    c = 0
    cols = []
    for clen in clens:
        cc = seq[c:c+clen]
        cols.append(cc)
        c = c + clen
    return cols 
    
if __name__ == '__main__':
    s = (0,1,2,3,4,5,6,7,8,9)
    print s
    for func in rowmaker, columnmaker:
	print
	print "testing function %s with sequence %s..." \
	      % (repr(func.__name__), repr(s))
	for cols in range(1,len(s)+2):
	    print "%s column%s:" % (cols, (cols != 1 and "s") or ""), apply(func, (s, cols))

