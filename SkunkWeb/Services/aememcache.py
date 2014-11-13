"""

This service makes AE.Cache use a memcached backend rather than disk
for the component cache.

To turn this on, define memcacheCacheBackend to be a list of ip
address of memcache servers.  If it is None, this will fall back to
the usual skunk cache.

"""
import cPickle

import memcache

import AE.Cache
from Logger import logException, ERROR
import SkunkWeb.Configuration as C

C.mergeDefaults(memcacheCacheBackend=None,
                memcachePathPrefix='component_')

_clients={}
def _get_memcache_client():
    global _clients
    servers=C.memcacheCacheBackend
    if not servers:
        return None
    servers.sort()
    servers=tuple(servers)
    try:
        return _clients[servers]
    except KeyError:
        client=memcache.Client(servers, False)
        _clients[servers]=client
        return client

def store_component(path, value, svr):
    client=_get_memcache_client()
    if not client:
        return AE.Cache._disk_store(path, value, svr)
    fullpath=C.memcachePathPrefix+path
    pickled=cPickle.dumps(value, cPickle.HIGHEST_PROTOCOL)
    exp_time=value.get('exp_time', 0)
    try:
        res=client.set(fullpath, pickled, exp_time)
    except:
        ERROR("exception storing component at path %s" % fullpath)
        logException()

def load_component(path, svr):
    client=_get_memcache_client()
    if not client:
        return AE.Cache._disk_load(path, svr)
    fullpath=C.memcachePathPrefix+path
    try:
        data=client.get(fullpath)
    except:
        ERROR("exception reaching memcached")
    else:
        if data is not None:
            return cPickle.loads(data)
        


AE.Cache._disk_load=AE.Cache._loadCachedComponent
AE.Cache._disk_store=AE.Cache._storeCachedComponent
AE.Cache._loadCachedComponent=load_component
AE.Cache._storeCachedComponent=store_component
    
