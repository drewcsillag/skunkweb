import base64
import cPickle
import md5

class InvalidStateException(Exception): pass

class InPageStateManager:
    """
    responsible for holding and marshalling into
    a value that can be placed securely in a hidden field
    some value.  The nonce is used to generate a verifiable
    hash.  If you want to further encrypt the pickled value
    of the state, use a stateEncryptor, which should have
    encrypt() and decrypt() methods (like the class in aesencrypt,
    or a rotor object).  The stateVariable is the cgi key
    used for retrieving and setting state.
    """
    def __init__(self,
                 nonce,
                 stateEncryptor=None,
                 stateVariable='_state'):
        self.state = {'stack' : []}
        self.encryptor=stateEncryptor
        self.stateVariable=stateVariable

    def write(self):
        s = cPickle.dumps(self.state, 1)
        if self.encryptor:
            s=self.encryptor.encrypt(s)
        hash = md5.md5(self.nonce + s).digest()
        outv = base64.encodestring(hash + s)
        return ''.join(outv.split('\n'))

    def read(self, statestr):
        inv = base64.decodestring(statestr)
        hash, pick = inv[:16], inv[16:]
        nhash = md5.md5(self.nonce + pick).digest()
        if nhash != hash:
            raise InvalidStateException, 'state has been tampered with'
        if self.encryptor:
            pick=self.encryptor.decrypt(pick)
        self.state = cPickle.loads(pick)

    def setstate(self, cgiarguments):
        try:
            statestr = cgiarguments[self.stateVariable]
        except KeyError:  # no state to get
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
