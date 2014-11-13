# Time-stamp: <03/04/15 00:13:38 smulloni>
#
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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

    
