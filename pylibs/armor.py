#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
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
                   
