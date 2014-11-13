"""

This service uses Ben Bangert's Routes package (http://routes.groovie.org/)
to map urls to controllers/actions.

To use it, define the config variable "routes" in sw.conf as a list
of argument sets that can be passed to routes.base.Mapper.connect.  An argument
set can be one of:

   - lists/tuples, passed as positional arguments
   - dictionaries, passed as keyword arguments
   - a 2-list/tuple, ((), {}) passed as positional + keyword arguments

This service requires the context and controllers mvc services.
"""

import _shared
from routes.base import Mapper
from routes.util import url_for, redirect_to
from routes import request_config
import SkunkWeb.Configuration as Cfg
from SkunkWeb import Context
from web.protocol import RouteConnection
from SkunkWeb.constants import WEB_JOB

# the controller service is required
import controller

# make sure that the context object is installed
import context

from mvc.log import debug

__all__=['url_for', 'redirect_to']

Cfg.mergeDefaults(routes=[])

def _do_redirect(url):
    Context.Connection.redirect(url)

def routing_hook(connection, sessionDict):
    if not Cfg.MvcOn:
        return
    debug("in routing hook")
    # initialize routes request config
    rcfg=request_config()
    rcfg.redirect=_do_redirect
    rcfg.mapper=map=Mapper()
    rcfg.host=connection.host
    if connection.env.get('HTTPS', False):
        rcfg.protocol='HTTPS'
    else:
        rcfg.protocol='HTTP'
        
    # initialize the map
    for r in Cfg.routes:
        if isinstance(r, dict):
            map.connect(**r)
        elif isinstance(r, (list, tuple)):
            if (len(r)==2 and
                isinstance(r[0], (list, tuple)) and
                isinstance(r[1], dict)):
                map.connect(*r[0], **r[1])
            else:
                map.connect(*r)
        else:
            raise ValueError, "wrong arguments for connect()"

    map.create_regs(Cfg.controllers.keys())

    # test the url with the map
    res=rcfg.mapper_dict=map.match(connection.uri) or {}
    debug("performed routing match")
    # put the result if the session dict
    if res:
        debug("have routing match!")
        res=res.copy()
        debug("result dict: %s", res)
        controller=res.pop('controller', None)
        action=res.pop('action', None)
        sessionDict['CONTROLLER']=controller
        sessionDict['ACTION']=action
        sessionDict['CONTROLLER_ARGS']=res
        
                
glob='%s*' % WEB_JOB
RouteConnection[glob]=routing_hook
