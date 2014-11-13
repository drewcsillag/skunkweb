# Time-stamp: <02/07/29 12:41:03 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

from SkunkWeb import ServiceRegistry, Configuration
from SkunkWeb.LogObj import DEBUG, logException
import AE.Cache
import vfs
import os, sys
import cStringIO
import rfc822

ServiceRegistry.registerService('pycgi')
PYCGI=ServiceRegistry.PYCGI

# use templating's 404 handler if it is already imported,
# or is about to be loaded, to the extent possible to determine.
# this is cut-and-pasted from rewrite.py, which is unfortunate;
# I should put this is a separate place, but where?

if sys.modules.has_key('templating') \
       or 'templating' in Configuration.services:
    import templating
    fourOhFourHandler=templating.Handler.fourOhFourHandler

else:
    def fourOhFourHandler(connection, sessionDict):
        connection.setStatus(404)
        connection.responseHeaders['Content-Type']='text/html'
        connection.write(
            'Sorry the requested document (<tt>%s</tt>) is not available' \
            % connection.uri)
        return  connection.response()

def _swap_streams(conn, saved=None):
    if not saved:
        saved=sys.stdout, sys.stderr, sys.stdin
        sys.stdout=sys.stderr=cStringIO.StringIO()
        sys.stdin=cStringIO.StringIO(conn._stdin)
        DEBUG(PYCGI, conn._stdin)
        return saved
    else:
        new=(sys.stdout, sys.stderr, sys.stdin)
        (sys.stdout, sys.stderr, sys.stdin)=saved
        return new
    

def _processRequest(conn, sessionDict):
    DEBUG(PYCGI, "pycgi processing request")
    try:
        env=_fix(conn.env, conn.uri)
    except vfs.FileNotFoundException:
        DEBUG(PYCGI, "file not found!")
        return fourOhFourHandler(conn, sessionDict)
    DEBUG(PYCGI, "file evidently exists")
    oldpwd=os.getcwd()
    os.environ.update(env)
    # what to do with argv?
    save_argv=sys.argv
    sys.argv=[env['SCRIPT_NAME']]
    saved=_swap_streams(conn)
    try:
        try:
            (directory, file) = os.path.split(env['SCRIPT_FILENAME'])
            os.chdir(directory)
            DEBUG(PYCGI, "about to execfile %s" % file)
            execfile(file)
        except SystemExit:
            pass
        except:
            logException()
            raise
    finally:
        os.chdir(oldpwd)
        sys.argv=save_argv
        new=_swap_streams(conn, saved)
    new[0].seek(0)
    respp = rfc822.Message(new[0])
    for k,v in respp.items():
        conn.responseHeaders[k] = v
    conn.write(new[0].read())        
    return conn.response()

    
def _fix(dict, uri):
    DEBUG(PYCGI, "in _fix")
    nd = {}
    for k,v in dict.items():
        nd[str(k)] = str(v)
    translated=AE.Cache._fixPath(Configuration.documentRoot, uri)
    fullpath, extra=Configuration.documentRootFS.split_extra(translated)
    if not fullpath:
        raise vfs.FileNotFoundException, translated
    # file exists
    if extra:
        nd['PATH_INFO']='/%s' % extra
    nd['PATH_TRANSLATED']=translated
    nd['SCRIPT_FILENAME']=fullpath
    nd['SCRIPT_NAME']=fullpath[len(Configuration.documentRoot):]
    return nd

def __initHooks():
    import web.protocol
    import SkunkWeb.constants as co
    jobGlob=co.PYCGI_JOB
    web.protocol.HandleConnection[jobGlob]=_processRequest

__initHooks()
