#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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
# $Author$
# $Revision$
# Time-stamp: <01/05/04 15:28:13 smulloni>
########################################################################
import cPickle
from sessionHandler.Session import SessionStore
from PyDO import *
from SkunkWeb import Configuration
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
from SkunkWeb.LogObj import DEBUG

PICKLE=Configuration.SessionHandler_PGPickleColumn
TIMESTAMP=Configuration.SessionHandler_PGTimestampColumn
ID=Configuration.SessionHandler_PGIDColumn

_args={'host': Configuration.SessionHandler_PGHost,
       'db': Configuration.SessionHandler_PGDB,
       'user' : Configuration.SessionHandler_PGUser,
       'pass' : Configuration.SessionHandler_PGPass}
DBIInitAlias('sessionAlias',
             'pydo:postgresql:%(host)s:%(db)s:%(user)s:%(pass)s' % _args)

class _PGStore(PyDO):
    connectionAlias='sessionAlias'
    table=Configuration.SessionHandler_PGTable
    fields=(
        (ID, 'varchar(40)'),
        (PICKLE, 'text'),
        (TIMESTAMP, 'timestamp'))
    unique=['id']

    def updateValues(self, dict):
        if not dict.has_key(TIMESTAMP):
	    dict = dict.copy()
	    dict[TIMESTAMP] = SYSDATE
        return PyDO.updateValues(self, dict)    

class PostgreSQLSessionStoreImpl(SessionStore):

    def __init__(self, id):
        tmp=_PGStore.getUnique(**{ID:id})
        if tmp:
            self.__pydo=tmp
        else:
            self.__pydo=_PGStore.new(**{ID:id, 'refetch':1})
        DEBUG(SESSIONHANDLER,
              "creating session with store: %s" % self.__pydo.items())
    
    def load(self):
        self.__pydo[TIMESTAMP]=SYSDATE
        self.__pydo.commit()
        DEBUG(SESSIONHANDLER, str(self.__pydo.items()))
        gherkin=self.__pydo[PICKLE]
        if gherkin!=None:
            return cPickle.loads(gherkin)
        return {}

    def save(self, data):
        self.__pydo[PICKLE]=cPickle.dumps(data)
        self.__pydo.commit()

    def delete(self):
        self.__pydo.delete()
    
    def touch(self):
        self.__pydo[TIMESTAMP]=SYSDATE
        self.__pydo.commit()
    
