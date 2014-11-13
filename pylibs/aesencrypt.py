#! /usr/bin/env python
# Time-stamp: <02/11/29 21:42:30 smulloni>
"""
a convenience class for encrypting strings or
arbitrary length using AES.  Requires PyCrypto,
available at from http://www.amk.ca/python/code/crypto.html.
"""
import Crypto.Cipher.AES as AES
import md5
import os
import sys

class AESEncryptor:
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

    def encrypt(self, thing):
        thing=self._pad(thing)
        return AES.new(self.__key, AES.MODE_CBC, self.IV).encrypt(thing)

    def decrypt(self, encrypted):
        thing=AES.new(self.__key, AES.MODE_CBC, self.IV).decrypt(encrypted)
        return self._unpad(thing)


def encrypt_file(infp, outfp, key):
    if infp=='-':
        infp=sys.stdin
    else:
        infp=open(infp, 'rb')
        
    if  outfp=='-':
        outfp=sys.stdout
    else:
        outfp=open(outfp, 'wb')
    slurp=infp.read()
    encoder=AESEncryptor(key)
    inscrut=encoder.encrypt(slurp)
    outfp.write(inscrut)
    outfp.flush()
    outfp.close()

def decrypt_file(infp, outfp, key):
    if infp=='-':
        infp=sys.stdin
    else:
        infp=open(infp, 'rb')
        
    if  outfp=='-':
        outfp=sys.stdout
    else:
        outfp=open(outfp, 'wb')
    slurp=infp.read()
    encoder=AESEncryptor(key)
    inscrut=encoder.decrypt(slurp)
    outfp.write(inscrut)
    outfp.flush()
    outfp.close()
    
if __name__=='__main__':
    import getopt
    usage=("usage: %s [-h] [-x|-c] <input file> <output file>\n" \
           "where options are:\n" \
           "\t-h            print this help message\n" \
           "\t-x            decrypt\n" \
           "\t-c            encrypt (default)\n") % sys.argv[0]
    optlist, args=getopt.getopt(sys.argv[1:], "cxh")
    opts=dict(optlist)
    help=opts.has_key('-h')
    if help:
        print >> sys.stderr, usage
        sys.exit(1)
   
    decrypt=opts.has_key('-x')
    encrypt=opts.has_key('-c')
    if decrypt and encrypt:
        print >> sys.stderr, "decrypt and encrypt are mutually incompatible options!"
        print >> sys.stderr, usage
        sys.exit(1)
    if not (decrypt or encrypt):
        encrypt=1
    # verify files
    if len(args)==0:
        infp='-'
        outfp='-'
    elif len(args)==1:
        outfp='-'
        infp=args[0]
    else:
        infp, outfp=args[:2]
    if infp!='-':
        if not os.path.exists(infp):
            print >> sys.stderr, "file %s not found!" % infp
            print >> sys.stderr, usage
            sys.exit(1)
    import getpass
    key=getpass.getpass('encryption key:')
    if encrypt:
        encrypt_file(infp, outfp, key)
    else:
        decrypt_file(infp, outfp, key)
        
    
    
        
