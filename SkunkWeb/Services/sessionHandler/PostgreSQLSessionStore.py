#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# Time-stamp: <03/06/05 10:09:33 smulloni>
########################################################################

import cPickle
from sessionHandler.Session import SessionStore
from SkunkWeb import Configuration
# from SkunkWeb.ServiceRegistry import SESSIONHANDLER
# from SkunkWeb.LogObj import DEBUG
import PyPgSQLcache
from pyPgSQL.PgSQL import _quote
import time

class Store(SessionStore):

    setPickleSQL=("UPDATE %(table)s SET %(pickleCol)s='%(gherkin)s', %(timeCol)s = NULL"\
                  "WHERE %(idCol)s=%(id)s")

    insertPickleSQL="INSERT INTO %(table)s (%(idCol)s, %(pickleCol)s) VALUES (%(id)s, %(gherkin)s)"


    reapSQL="DELETE FROM %(table)s WHERE CURRENT_TIME - INTERVAL '%(timeout)s SECONDS' > %(timeCol)s"    

    def getConnection(self):
        return PyPgSQLcache.getConnection(Configuration.SessionHandler_PostgreSQLAlias)

    def escapeSQLString(self, s):
        return _quote(s)

    def _setPickle(self, sessionHash):
        db=self.getConnection()
        c=db.cursor()
        args={'id' : self.__id,
              'idCol' : self.idCol,
              'pickleCol' : self.pickleCol,
              'gherkin' : self.escapeSQLString(cPickle.dumps(sessionHash, 1)),
              'timeCol' : self.timeCol,
              'table': self.table}
        c.execute(self.setPickleSQL % args)
        if not c.rowcount:
            c.execute(self.insertPickleSQL % args)
        db.commit()
        self._lastTouched=int(time.time())
