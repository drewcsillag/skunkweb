import _shared
import SkunkWeb.Configuration as Cfg
from web.protocol import PreemptiveResponse, HandleConnection
from templating.Handler import _handleException
from SkunkWeb.constants import WEB_JOB
from SkunkWeb.LogObj import logException
from mvc.log import debug, info
from mvc.utils import is_exposed, _import_a_class
from mvc.base import Response
import types

Cfg.mergeDefaults(controllers={},
                  defaultErrorMimetype='text/html')

def _resolve_string(controllerName):
    try:
        c=_import_a_class(controllerName)
    except ImportError:
        logException()
        return None
    else:
        # do we need to instantiate one?
        # who says this needs to be a instance anyway?
        return c

def controllerHandler(connection, sessionDict):
    if not Cfg.MvcOn:
        return
    cname=sessionDict.get('CONTROLLER')
    data=sessionDict.get('CONTROLLER_ARGS')
    aname=sessionDict.get('ACTION')
    debug("do we have a controller? %s",  ('No', 'Yes')[bool(cname)])
    if cname:
        c=Cfg.controllers.get(cname)
        if c:
            if isinstance(c, basestring):
                # resolve it
                c=_resolve_string(c)
                if not c:
                    return
            if not aname:
                aname='index'
            meth=getattr(c, aname, None)
            if meth and not is_exposed(meth):
                info("request for method that isn't exposed, not honoring")
                meth=None
            if not meth:
                # look for a default method and pass
                # the action name in as a keyword argument
                data['action']=aname
                if callable(c):
                    meth=c
                else:
                    # "default" doesn't need to be exposed
                    meth=getattr(c, "default", None)
		    
            if meth:
                # some defaults
                connection.setStatus(200)
                connection.setContentType('text/html')
                try:
                    res=meth(**data)
                except PreemptiveResponse:
                    # not a problem, raise it
                    raise
                except Response, res:
                    res(connection)
                    return connection.response()
                except:
                    # OK, something bad.  This should be a server error.
                    return _handleException(connection)
                else:
                    if res:
                        if isinstance(res, basestring):
                            connection.write(res)
                        elif callable(res):
                            res(connection)
                        else:
                            # an iterable, hopefully
                            for thing in res:
                                connection.write(thing)
                        return connection.response()
                
                    
glob='%s*' % WEB_JOB
# go *before* the templating handlers
HandleConnection.addFunction(controllerHandler, glob, 0)


                    
                
                
