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
        f = self.authDict[user] = self._makeHash(user, password)

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

            
            
        
