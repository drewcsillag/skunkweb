# Time-stamp: <02/02/04 22:11:36 smulloni>

######################################################################## 
#  Copyright (C) 2002 Jocob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

import unittest
import os
from vfs import ShelfPathPropertyStore, ZODBPathPropertyStore, ZipFS



FOO_ZIP='/home/smulloni/workdir/skunkweb/pylibs/vfs/foo.zip'
FOO_LISTING=['/index.html', '/dammit', '/dammit/index.html']

class ZipTests(unittest.TestCase):

    def setUp(self):
        self.foo=ZipFS(FOO_ZIP)

    def testListing1(self):
        listing=self.foo.listdir('/')
        listing.sort()
        self.assertEquals(listing, ['dammit', 'index.html'])
        listing=self.foo.listdir('/dammit')
        listing.sort()
        self.assertEquals(listing, ['index.html'])

    def testExists1(self):
        for f in FOO_LISTING:
            assert self.foo.exists(f)
        for f in ['/doughnut', '/frogling/peach/lumpy/pie', 'pooh', '..']:
            assert not self.foo.exists(f)

class PathTests(unittest.TestCase):

    def setUp(self):
        # you have to start this up yourself for this to work.
        self.zodb_store=ZODBPathPropertyStore('/tmp/zeo_socket',
                                              'pps_store1')
        self.shelf_store=ShelfPathPropertyStore('/tmp/garbage')

    def test001_SetProperty(self):
        self.zodb_store.setproperty('/ingot/', 'value', 45)
        self.shelf_store.setproperty('/ingot/', 'value', 45)

    def test002_GetProperty(self):
        self.assertEquals(self.zodb_store.getproperty('/ingot/', 'value'), 45)
        self.assertEquals(self.shelf_store.getproperty('/ingot/', 'value'), 45)

    def test003_HasProperty(self):
        assert self.zodb_store.hasproperty('/ingot/', 'value')
        assert self.shelf_store.hasproperty('/ingot/', 'value')

    def test004_Acquire(self):
        self.assertEquals(self.zodb_store.acquire('/ingot/petunia/french/gorgon.pdf', 'value'), 45)
        self.assertEquals(self.shelf_store.acquire('/ingot/petunia/french/gorgon.pdf', 'value'), 45)
    
if __name__=='__main__':
    print "Running...."
    unittest.main()
