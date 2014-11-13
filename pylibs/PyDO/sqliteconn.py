# Time-stamp: <02/08/12 11:34:50 smulloni>
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>,
#                     Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#
########################################################################

import sqlite
import PyDBI

class PyDOSqlite:
    def __init__(self, connectArgs):
        self.bindVariables = 0
        if connectArgs.has_key('verbose') and connectArgs['verbose']:
            self.verbose=1
            del connectArgs['verbose']
        else:
            self.verbose=0
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
        if self.verbose:
            print "SQL> %s" % sql
        cur.execute(sql) #, values)
        result=cur.fetchall()

        if not result and cur.fetchone() in (None, (), []):
            return cur.rowcount
        fields=[x[0] for x in cur.description]
        if attributes is None:
            return result, fields
        return self.convertResultRows(fields, attributes, result)

    def convertResultRows(self, columnNames, attributes, rows):
        newresult=[]
        for row in rows:
            d={}
            for item, desc in zip(row, columnNames):
                a=attributes.get(desc)
                d[desc]=self.__convert(a, item)
            newresult.append(d)
        return newresult

    def __convert(self, attribute, item):
        # add conversions here TBD
        return item
        
    def resetQuery(self): pass
    def getSequence(self, name): pass
    
    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def getAutoIncrement(self, name):
        return self.conn.db.sqlite_last_insert_rowid()
    
    def typeCheckAndConvert(self, value, attributeName, attrDbType):
        """check values type to see that it is valid and subsequently
        do any conversion to value necessary to talk to the database with
        it, i.e. mxDateTime to database date representation"""
        pass
        
    def postInsertUpdate(self, PyDOObject, dict, isInsert): pass



def test():
    import PyDO
    import PyDBI

    PyDBI.DBIInitAlias('test', {'driver' : 'sqlite',
                                'db' : '/home/smulloni/testdb',
                                'verbose' : 1})

    class Contact(PyDO.PyDO):
        connectionAlias="test"
        table='Contact'
        fields= (
            ('id', 'integer'),
            ('firstname', 'text'),
            ('lastname', 'text'),
            ('home_email', 'text') )
        unique=['id']
        auto_increment={'id' : 'Contact'}

    contacts=Contact.getSome()
    for c in contacts:
        print c.dict()
    while 1:
        answer=raw_input("new contact? [y/N]").lower()
        if not answer.startswith('y'):
            return
        firstname=raw_input('first name: ')
        lastname=raw_input('last name: ')
        email=raw_input('email: ')
        c=Contact.new(refetch=1, firstname=firstname,
                      lastname=lastname, home_email=email)
        print c.dict()
        answer=raw_input("OK? [y/N]").lower()
        if answer.startswith('y'):
            c.commit()
        else:
            c.rollback()
    

    
