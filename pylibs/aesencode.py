# Time-stamp: <02/11/20 00:10:30 smulloni>
# $Id$
"""
a convenience class for encoding strings or
arbitrary length using AES.  Requires PyCrypto,
available at from http://www.amk.ca/python/code/crypto.html.
"""
import Crypto.Cipher.AES as AES
import md5


class AESEncoder:
    def __init__(self, key, IV=None):
        self.key=key
        self.__key=md5.md5(key).digest()
        if IV==None:
            IV=self.key[:16].ljust(16)
        self.IV=IV

    def _pad(self, thing):
        s='%dX%s' % (len(thing), thing)
        ls=len(s)
        m=ls % AES.block_size
        return s.ljust(ls-m + AES.block_size)

    def _unpad(self, padded):
        xind=padded.find('X')
        num=int(padded[:xind])
        return padded[xind+1:xind+1+num]

    def encode(self, thing):
        thing=self._pad(thing)
        return AES.new(self.__key, AES.MODE_CBC, self.IV).encrypt(thing)

    def decode(self, encoded):
        thing=AES.new(self.__key, AES.MODE_CBC, self.IV).decrypt(encoded)
        return self._unpad(thing)
