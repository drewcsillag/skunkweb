import base64
import cPickle
import md5

class InPageStateManager:
    def __init__(self, nonce):
        self.state = {'stack' : []}

        #these are non-persisted state items
        self.nonce = nonce
        self.invalidFields = None
        self.invalidOtherFields = None
        
    def asHTML(self):
        s = cPickle.dumps(self.state, 1)
        hash = md5.md5(self.nonce + s).digest()
        outv = base64.encodestring(hash + s)
        outv = ''.join(outv.split('\n'))
        return '<input type=hidden name=_state value="%s">' % outv

    def setstate(self, cgiarguments):
        try:
            state = cgiarguments['_state']
        except:  #no state to get
            return
        inv = base64.decodestring(state)
        hash, pick = inv[:16], inv[16:]
        nhash = md5.md5(self.nonce + pick).digest()
        if nhash != hash:
            return 'state has been tampered with'
        self.state = cPickle.loads(pick)
        
    def push(self, formname):
        stack = self.state['stack']
        stack.append(formname)

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
