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
import base64
import random
import time

def armor(nonce, value):
    random.seed(time.time())
    svs = []
    for i in range(4):
        svs.append(chr(random.randrange(0,256)))
        
    salt = ''.join(svs)
    
    digest = sha.sha(salt + value + nonce).digest()
    return base64.encodestring(salt + value + digest)

def dearmor(nonce, value):
    try:
        return dearmor_detail(nonce, value)
    except:
        return None
    
def dearmor_detail(nonce, value):
    try:
        value = base64.decodestring(value)
    except: #value string is bogus
        raise "bogus"
    
    salt = value[:4]
    digest = value[-20:]
    value = value[4:-20]

    ndigest = sha.sha(salt + value + nonce).digest()
    if ndigest != digest:
        raise "invalidhash"

    return value
                   
