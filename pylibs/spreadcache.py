# Time-stamp: <03/04/15 00:13:38 smulloni>
# $Id$
#
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
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

import spread

class SpreadAlias(object):
    """
    a cache for spread mailboxes.
    """
    _aliases={}
    def __init__(self,
                 alias,
                 spread_name="",
                 private_name="",
                 priority=0,
                 membership=1,
                 groups=(),
                 verify_func=None):
        if self._aliases.has_key(alias):
            raise ValueError, "alias %s already initialized"
        self.alias=alias
        self.spread_name=spread_name
        self.private_name=private_name
        self.priority=priority
        self.membership=membership
        self.groups=groups
        self.verify_func=verify_func
        self._mbox=None
        self._aliases[alias]=self

    def _real_connect(self):
        self._mbox=spread.connect(self.spread_name,
                                  self.private_name,
                                  self.priority,
                                  self.membership)
        if self.groups:
            for g in self.groups:
                self._mbox.join(g)

    def get_mailbox(cls, alias):
        try:
            al=cls._aliases[alias]
        except KeyError:
            raise ValueError, \
                  "alias %s is not initialized" % alias
        if al._mbox is None:
            al._real_connect()
        elif al.verify_func:
            try:
                al.verify_func(al._mbox)
            except spread.error: # possibly others?
                al._mbox=None
                al._real_connect()
        return al._mbox

    get_mailbox=classmethod(get_mailbox)
            
get_mailbox=SpreadAlias.get_mailbox

def initAlias(*args, **kwargs):
    SpreadAlias(*args, **kwargs)


def _test(do_init=1):
    if do_init:
        initAlias('jones',
                  groups=('hi',),
                  verify_func=lambda x: x.poll(),
                  membership=0)
    mbox=get_mailbox('jones')
    mess='hey there jones: %d' % do_init
    mbox.multicast(spread.RELIABLE_MESS, 'hi', mess)
    m=mbox.receive()
    print m.message
    assert m.message==mess
    
    if do_init:
        # test that the verify func restores the connection
        mbox.disconnect()
        del mbox
        _test(0)

    
