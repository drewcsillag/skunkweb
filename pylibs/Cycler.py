#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
This module provides a class which will "cycle"
over a list or tuple of items, looping back to the
start of the sequence as necessary. Use this Cycler
class for things like alternating the colors of HTML
table rows:


import Cycler
cyc = Cycler.Cycler( ('#CCCCFF', '#9999FF') )
rows = get_my_list_of_table_rows()
for row in rows:
    print '&lt;td bgcolor="%s"&gt;%s&lt;td&gt;' % \
	  (cyc.next(), row)

"""

from types import TupleType, ListType
from whrandom import randint

class Cycler:
    """
    Implements an cycler over a sequence of items.
    """
    def __init__(self, items, randomize=0):
	"""
	items is a list or tuple of items to "cycle through".
	randomize, if false, means that as the cycler iterates
	over objects, it starts at the beginning of items,
	walks through the sequence in order, and returns to the start of
	sequence after it has reached the last item.
	If randomize is true, the cycler picks a random item in
	the sequence as the "start item". Each iteration then jumps to
	another, randomly chosen item in the sequence that is not
	the same item as before. Thus, no item will be used twice in
	a row.
	"""
	if type(items) not in (TupleType, ListType):
	    raise TypeError, "items %s must be a list or tuple" % repr(items)
	if not items:
	    raise ValueError, "items %s must not be empty" % repr(items)
	if len(items) < 2:
	    raise ValueError, "items %s must have more than one item" % repr(items)
        self.items = items
	self.randlen = len(items) - 1
	self.randomize = randomize
	if randomize:
	    self.pointer = randint(0, self.randlen)
	else:
	    self.pointer = 0

    def reset(self, randomize=None):
	"""
	Resets the cycler to the "beginning". The randomize
	argument lets you specify whether the cycler should
	be a randomized cycler after reset. It permanently changes the
	cycler's current randomize setting. If randomize is
	None, no change is made to the cycler's randomize
	setting.
	"""
	if randomize is None: randomize = self.randomize
	if randomize:
	    self.pointer = randint(0, self.randlen)
        else:
	    self.pointer = 0

    def next(self, randomize=None):
	"""
	Returns the next item in the cycler's sequence, according
	to the cycler's settings. If randomize is None,
	the cycler uses its randomize setting. If true, the cycler
	selects this next item in a random fashion, but does not
	permanently change the cycler's randmoize settings. If false,
	the cycler returns the next item in the sequence without randomizing,
	but does not permanently change the cycler's randomize settings.
	"""
	result = self.items[self.pointer]
	# now update pointer
	if randomize is None: randomize = self.randomize
	if randomize:
	    newptr = self.pointer
	    while newptr == self.pointer:
		newptr = randint(0, self.randlen)
        else:
	    newptr = self.pointer + 1
	    if newptr > self.randlen:
		newptr = 0
	self.pointer = newptr
	return result

if __name__ == '__main__':
    # test bogus instantiation
    try: i = Cycler('not a tuple/list')
    except TypeError: pass
    try: i = Cycler([])
    except ValueError: pass

    # test non-random cycler
    items = ['foo', 'bar', 'baz']
    print "Making non-random cycler for %s" % repr(items)
    i = Cycler(items)
    print "doing 30 iterations on cycler..."
    for x in range(30):
	print i.next()

    # randomized calls of non-random cycler
    print "now calling 30 randomized items from non-random cycler"
    for x in range(30):
	print i.next(randomize=1)
    # test full random cycler
    print "Making fully random cycler for %s" % repr(items)
    i = Cycler(items, randomize=1)
    print "doing 30 iterations on cycler..."
    for x in range(30):
	print i.next()
    print "resetting random cycler with randomize=0"
    i.reset(randomize=0)
    print "now calling 30 non-random items from random cycler"
    for x in range(30):
	print i.next(randomize=0)

