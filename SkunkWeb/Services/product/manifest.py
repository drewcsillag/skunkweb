# Time-stamp: <02/02/23 02:05:51 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

import os, time, types

class ManifestException(Exception): pass

MANIFEST_FILE='MANIFEST'

def _assert(bool, message):
    if not bool:
        raise ManifestException, "invalid manifest: %s" % message

MANIFEST_DEFAULTS={ 'docroot' : 'docroot',
                    'libs' : 'libs',
                    'dependencies' : (),
                    'services' : ()}
                    
def read_manifest(manifest_bytes):    
    d={}
    d.update(MANIFEST_DEFAULTS)
    exec manifest_bytes in {}, d
    _checkData(d)
    return d

def _checkData(manifestData):
    _assert(manifestData.has_key('version'), "no version specified")
    # more checks here ?? TBD

def write_manifest(file, data, overwrite=0, comments=()):
    _checkData(data)
    if os.path.exists(file) and not overwrite:
        raise ManifestException, "will not overwrite existing manifest at %s" % file
    f=open(file, 'w')
    if comments:
        for c in comments:
            f.write('# %s\n' % c)
    for k, v in data.items():
        f.write('%s = %s\n' % (k, repr(v)))
    f.write("# this SkunkWeb product manifest generated on %s\n" % time.asctime())
    f.close()

def generate_manifest(productdir,
                      version,
                      overwrite=0,
                      docroot=None,
                      libs=None,
                      services=None,
                      dependencies=None):

    manifestpath=os.path.join(productdir, MANIFEST_FILE)
    # eliminate defaults
    d={'version' : version, 'overwrite' : overwrite}
    if docroot!=None:
        d['docroot']=docroot
    if libs!=None:
        d['libs']=libs
    if services!=None:
        d['services']=services
    if dependencies!=None:
        d['dependencies']=dependencies
    write_manifest(manifestpath, d)
    
    
__all__=['read_manifest',
         'write_manifest',
         'MANIFEST_FILE',
         'MANIFEST_DEFAULTS',
         'ManifestException']

