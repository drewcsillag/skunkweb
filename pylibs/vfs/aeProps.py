# $Id$
# Time-stamp: <02/02/05 02:48:44 smulloni>

######################################################################## 
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
########################################################################

"""
a read-only path property store (setproperty and delproperty are unimplemented!)
that uses AE python data components to store the properties.  Properties are hence
set by editing those files.  Useful for application configuration where programmatic
setting of properties is not desired and the ability for an admin to edit them by
hand is; obviously a fragile mechanism.
"""

from vfs import PathPropertyStore, VFSException
import AE.Cache as Cache
import AE.Component as Component
from AE.cfg import Configuration
from skunklib import normpath2 as _normpath
import os.path
from DT import DT_DATA

class AEPathPropertyStore(PathPropertyStore):
    
    def __init__(self, compname='pps_config', cache=None):
        self.__compname='%s.pydcmp' % compname
        self.cache=cache

    def __splitpath(self, path):
        d, fname=os.path.split(path)
        if not fname and d=='/':
            fname='/'
        return d, fname

    def getproperty(self, path, property):
        try:
            return self.properties(path)[property]
        except KeyError:
            raise KeyError, property
            
    def properties(self, path):
        path=_normpath(path)
        d, fname=self.__splitpath(path)
        comppath=os.path.join(d, self.__compname)
        try:
            db=Component.callComponent(comppath,
                                       {},
                                       self.cache,
                                       DT_DATA)
        except VFSException:
            return {}                
        if type(db) != type({}):
            raise VFSException, "corrupted or inappropriate data in %s" % comppath
        props=db.get(fname, {})
        if type(props) != type({}):
            raise VFSException, "corrupted or inappropriate data in %s" % comppath
        return props
                            

    def hasproperty(self, path, property):
        props=self.properties(path)
        return props.has_key(property)


            
########################################################################
# $Log$
########################################################################




    
    
