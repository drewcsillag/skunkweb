import base64
import cPickle
from md5 import md5

class InvalidStateException(Exception): pass

class ArmorEncoder:
    def __init__(self, nonce):
        self.nonce=nonce
        
    def encode(self, thing):
        s = cPickle.dumps(thing, 1)
        hash = md5(self.nonce + s).digest()
        outv = base64.encodestring(hash + s)
        return ''.join(outv.split('\n'))

    def decode(self, thingstr):
        inv = base64.decodestring(thingstr)
        hash, pick = inv[:16], inv[16:]
        nhash = md5.md5(self.nonce + pick).digest()
        if nhash != hash:
            raise InvalidStateException, 'state has been tampered with'
        return cPickle.loads(pick)
    
try:
    import Crypto.Cipher.AES as AES
except ImportError:
    AES=None

if AES:
    class AESEncoder:
        def __init__(self, key, IV=None):
            self.key=key
            self.__key=md5(key).digest()
            if IV=None:
                IV=self.key[:16].ljust(16)
            self.aes=AES.new(self.__key, AES.MODE_CBC, IV)

        def _pad(self, thing):
            s='%dX%s' % (len(thing), thing)
            ls=len(s)
            m=ls % AES.block_size
            return s.ljust(ls-m + AES.block_size)

        def _unpad(self, padded):
            xind=s.find('X')
            num=int(s[:xind])
            return s[xind+1:xind+1+num]
         

        def encode(self, thing):
            thing=self._pad(thing)
            return self.aes.encrypt(thing)

        def decode(self, encoded):
            thing=self.aes.decrypt(encoded)
            return self._unpad(thing)
            


class InPageStateManager:
    def __init__(self, nonce, stateVariable='_state'):
        self.state = {'stack' : []}

        #these are non-persisted state items
        self.nonce = nonce
        self.stateVariable=stateVariable

        
    def write(self):
        s = cPickle.dumps(self.state, 1)
        hash = md5.md5(self.nonce + s).digest()
        outv = base64.encodestring(hash + s)
        return ''.join(outv.split('\n'))

    def read(self, statestr):
        inv = base64.decodestring(statestr)
        hash, pick = inv[:16], inv[16:]
        nhash = md5.md5(self.nonce + pick).digest()
        if nhash != hash:
            raise InvalidStateException, 'state has been tampered with'
        self.state = cPickle.loads(pick)

    def setstate(self, cgiarguments):
        try:
            statestr = cgiarguments[self.stateVariable]
        except:  # no state to get
            return
        self.read(statestr)
        
    def push(self, formdata):
        stack = self.state['stack']
        stack.append(formdata)

    def pop(self):
        stack = self.state['stack']
        return stack.pop(stack)

    def peek(self):
        return self.state['stack'][-1]
        
    def __setitem__(self, k, v):
        self.state[k] = v

    def __getitem__(self, k):
        return self.state[k]

    def get(self, k, default=None):
        return self.state.get(k, default)
