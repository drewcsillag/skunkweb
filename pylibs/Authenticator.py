#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import sha
from random import randint

class Authenticator:
    def _makeHash(self, user, password, salt = None):
        if salt is None:
            salt = "%04X" % randint(0,4095)
        chash = sha.sha('%s:%s%s' % (user, salt, password)).digest()
        return salt+''.join(["%02X" % ord(i) for i in chash])

    def authenticate(self, user, password):
        if not user or not password:
            return
        t = self.getHashBits(user)
        if t==None:
            return
        salt, hash = t[:4], t[4:]
        if not hash:
            return
        if self._makeHash(user, password, salt) == (salt+hash):
            return 1

    def getHashBits(self, user):
        raise NotImplementedError
    
class PreloadedAuthenticator(Authenticator):
    def __init__(self, authDict = {}):
        self.authDict = authDict
        
    def setUserPassword(self, user, password):
        self.authDict[user] = self._makeHash(user, password)

    def getHashBits(self, user):
        return self.authDict.get(user)

class FileAuthenticator(PreloadedAuthenticator):
    def __init__(self, filename):
        self.file = filename
        PreloadedAuthenticator.__init__(self)
        for i in open(filename).readlines():
            i=i.strip()
            if not i or i[0] == '#':
                continue
            colidx = i.rfind(':')
            if colidx == -1:
                continue
            name = i[:colidx]
            hash = i[colidx+1:]
            self.authDict[name] = hash

    def dump(self):
        f = open(self.file, 'w')
        for i in self.authDict.items():
            f.write('%s:%s\n' % i)
        f.close()

            
            
        
