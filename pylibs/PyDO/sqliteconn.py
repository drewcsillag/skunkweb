# Time-stamp: <02/08/06 23:56:25 smulloni>
# $Id$
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>,
#                     Andrew T. Csillag <drew_csillag@geocities.com>
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

import sqlite
import PyDBI

class PyDOSqlite:
    def __init__(self, connectArgs):
        self.bindVariables = 0
        self.conn=sqlite.connect(**connectArgs)

    def getConnection(self):
        return self.conn
    
    def bindVariable(self): pass
        
    def sqlStringAndValue(self, val, attributeName, dbtype):
        """Returns a sql string and a value.  The literal is to be put into
	the sql query, the value should is put into the value list that is
	subsequently passed to execute().

        The reason for this is for example, using bind variables in the
        generated sql, you want to return a bind variable string and the
        value to be passed.  If doing such things requires state, you can
        clear it in resetQuery().

        """
        return repr(val), None

    def execute(self, sql, values, attributes):
        cur=self.conn.cursor()
        cur.execute(sql, values)
        result=cur.fetchall()
        if not result and None==cur.fetchone():
            return cur.rowcount
        if attributes is None:
            return result, [x[0] for x in cur.description]
        fields=[x[0] for x in cur.description]
        return self.convertResultRows(fields, attributes, result)

    def convertResultRows(self, columnNames, attributeKinds, rows):
        newresult=[]
        for row in rows:
            d={}
            for item, desc in zip(row, columnNames):
                a=attributes.get(desc)
                d[desc]=self.__convert(a, item)
            newresult.append(d)
        return newresult

    def __convert(attribute, item):
        # add conversions here TBD
        return item
        
    def resetQuery(self): pass
    def getSequence(self, name): pass
    
    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def getAutoIncrement(self, name):
        cur=self.conn.cursor()
        cur.execute('select max(rowid) from %s' % name)
        return int(cur.fetchone()[0])
    
    def typeCheckAndConvert(self, value, attributeName, attrDbType):
        """check values type to see that it is valid and subsequently
        do any conversion to value necessary to talk to the database with
        it, i.e. mxDateTime to database date representation"""
        pass
        
    def postInsertUpdate(self, PyDOObject, dict, isInsert): pass



def test():
    import PyDO
    import PyDBI

    DBIInitAlias('test', {'driver' : 'sqlite', 'db' : '/home/smulloni/testdb'})

    class Contact(PyDO.PyDO):
        connectionAlias='test'
        fields=(
            ('id', 'integer'),
            ('firstname', 'text'),
            ('lastname', 'text'),
            ('home_email', 'text'))

    
