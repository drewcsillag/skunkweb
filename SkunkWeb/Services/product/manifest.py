# $Id: manifest.py,v 1.1 2002/02/20 04:54:14 smulloni Exp $
# Time-stamp: <02/02/23 02:05:51 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
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

