from Session import SessionStore
import AE.Cache
import SkunkWeb.Configuration as C
import os
import time
import errno

class Store(SessionStore):
    def __init__(self, id):
        self.id=id

    def componentPath(self):
        return '%s/%s' % (C.SessionHandler_AECacheSessionPath,
                          self.id)
    

    def load(self):
        res=AE.Cache.getCachedComponent(self.componentPath(), {}, -1)
        if res and res[0] and res[0].valid:
            return res[0].out
        return {}

    def save(self, data):
        AE.Cache.putCachedComponent(self.componentPath(),
                                    {},
                                    data,
                                    time.time()+C.SessionTimeout)
    def delete(self):
        #AE.Cache.clearCache(self.componentPath(), {}, 1)
        cachepath, srv, fk=AE.Cache._genCachedComponentPath(self.componentPath(), {})
        # there may be a key file.
        keypath=cachepath[:-5]+'key'
        for f in cachepath, keypath:
            try:
                os.unlink(f)
            except OSError, e:
                if e.errno==errno.ENOENT:
                    pass
                else:
                    raise


    def touch(self):
        cachepath, srv, fk=AE.Cache._genCachedComponentPath(self.componentPath(), {})
        curtime=time.time()
        os.utime(cachepath, (curtime, curtime))

    def lastTouched(self):
        cachepath, srv, fk=AE.Cache._genCachedComponentPath(self.componentPath(), {})
        try:
            return int(os.path.getmtime(cachepath))
        except OSError, e:
            if e.errno==errno.ENOENT:
                return int(time.time())
            else:
                raise

    def reap(self):
        pass
