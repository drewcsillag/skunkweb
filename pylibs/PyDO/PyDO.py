#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
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
import string
import sys
import types
from static import *
import operators

##_oldField=operators.FIELD
##class FIELD(_oldField):
##    def __init__(self, fieldname):
##        _oldField.__init__(self, fieldname)
##        # look into PyDO object calling this one, if any
##        frame=sys._getframe(1)
##        print frame.f_locals
##        callingSelf=frame.f_locals.get('self')
##        self.dbtype=None
##        self.dbi=None
##        if callingSelf:
##            print "found calling self: %s" % callingSelf
##            if hasattr(callingSelf, '__class__'):
##                callingClass=callingSelf.__class__
##                print "calling class: %s" % callingClass
##                self.dbtype=callingClass.fieldDict.get(self.fieldname)
##                self.dbi=callingClass.getDBI()

##operators.FIELD=FIELD
##del FIELD

PyDOError = "PyDO.Error"

from PyDBI import *

class NOT:
    def __init__(self, val):
        self.val = val

#defaults for the attributes in dataclasses that we scan for
_dataClassDefaults = {
    'connectionAlias': None,
    'table': None,
    'mutable': 1,
    'fields': (),
    'unique': [],
    'sequenced': {},
    'auto_increment': {},
    }

class PyDOBase(static):
    """
    A stripped down PyDO class, useful for backing by stored procs.
    This has no SQL generation facilities other than those provided by
    going directly to the connection.

    The only thing we really presume is that there is a connection to
    the database and some fields that we know about.  We then provide dict
    methods and a hook to make it so you can update values (if you want
    it to be mutable).
    """
    mutable = 0 # we have nothing of interest!  We're not instantiable anyway

    def __init__(self, dict):
        self._dict = dict

    def __repr__(self):
        return '<PyDO %s data class instance>' % self._klass._klass
        
    def static___class_init__(self):
        static.static___class_init__(self)
        if self._klass == 'PyDOBase':
            self._isRootClass = 1
            self._instantiable = 0
            return
        
        self._isRootClass = 0
        dict = self._dict

        #get class attributes (connAlias, fields, etc.)
        cid = {}
        for k, v in _dataClassDefaults.items():
            if dict.has_key(k):
                cid[k] = dict[k]
        if not cid.has_key('fields'):
            cid['fields'] = ()
            
        #do our attribute inheritance here
        fieldDict = {}
        scid = {}
        connAlias = None
        unique = []
        sequenced = {}
        proxyClass = None
        table = None
        
        scl = list(self._superClasses)
        scl.reverse()
        for sc in scl:
            if Sissubclass(sc, PyDOBase):
                if not sc._isRootClass:
                    fieldDict.update(sc.fieldDict)
                    connAlias = sc.connectionAlias
                    unique = sc.unique
                    sequenced = sc.sequenced
                    table = sc.table
                #else, is the PyDO root class instance, ignore
            else:
                raise TypeError, ("cannot inherit from class %s that "
                                  "isn't a subclass of PyDO" % bc)

        if type(cid['fields']) != type(()):
            raise TypeError, 'fields must be defined as a tuple of tuples'
        for kvp in cid['fields']:
            if type(kvp) != type(()):
                raise TypeError, 'fields must be defined as a tuple of tuples'
            k, v = kvp
            fieldDict[k] = v

        scid['connectionAlias'] = connAlias
        scid['unique'] = unique
        scid['sequenced'] = sequenced
        scid['table'] = table
        scid.update(cid)
        scid['fields'] = fieldDict.items()
        scid['fieldDict'] = fieldDict

        for k, v in _dataClassDefaults.items():
            if not scid.has_key(k):
                scid[k] = v
        
        self.__dict__.update(scid)
        #am I instantiable?
        #would I normally be instantiable?
        normallyInstantiable = (self.table
                                and self.connectionAlias
                                and self.fields)
        if dict.has_key('_instantiable'): #did they override what I think?
            self._instantiable = dict['_instantiable']
        else:
            self._instantiable = normallyInstantiable
        
        #check that static methods don't clash with instance methods
        #and vice versa
        m = self._staticMethods.keys()
        for k in self._instanceMethods.keys():
            #if same method name in both static and instance methods, barf
            if k in m: 
                raise TypeError, ('method %s in class %s defined with diff'
                                  'ering staticity to inherited '
                                  'method') % (k, self._klass)
        
    def static_getDBI(self):
        """return the database interface"""
        conn = DBIGetConnection(self.connectionAlias)
        conn.resetQuery()
        return conn

    #easy access to commit and rollback
    def static_commit(self):
        """commit the transaction"""
        self.getDBI().commit()

    def static_rollback(self):
        """rollback the current transaction"""
        self.getDBI().rollback()
    
    #dict methods
    def __getitem__(self, item):
        return self._dict[item]

    def __setitem__(self, item, val):
        return self.update({item: val})

    def items(self):
        """returns a list of key/value tuples"""
        return self._dict.items()

    def copy(self):
        """returns a copy of self"""
        return PyDOProxy(self._klass, self._dict.copy())

    def has_key(self, key):
        """returns 1 if I have that key"""
        return self._dict.has_key(key)

    def keys(self):
        """returns a list my keys"""
        return self._dict.keys()
    
    def values(self):
        """returns my values"""
        return self._dict.values()
    
    def get(self, item, default = None):
        """returns self[item] if it exists, otherwise returns default"""
        return self._dict.get(item, default)
    
    def update(self, dict):
        """updates self with the key/value pairs in dict"""
        for k, v in dict.items():
            if not self.fieldDict.has_key(k):
                raise KeyError, 'object %s has no field %s' % (
                    self._klass, k)

        self.updateValues(dict)
        self._dict.update(dict)

    def updateValues(self, dict):
        raise NotImplementedError, 'no way to update'

    def dict(self):
        """return a dictionary of my field values"""
        return self._dict.copy()

    def __cachekey__(self):
        return self._dict
    
class PyDO(PyDOBase):
    """
    The base metaclass instance that provides the base static and instance
    methods for PyDO classes.
    """
    ##############################
    ## PyDO static methods
    ##############################

    def static_getColumns(self, qualified = None):
        """return a list of column names for this data class.
        If qualified is some true value, qualify each column name
        with the tablename.
        """
        if not qualified:
            return self.fieldDict.keys()
        return map(lambda x, y=self.getTable(): '%s.%s' % (y,x),
                   self.fieldDict.keys())

    def static_getTable(self):
        """return the table name for this entity"""
        return self.table

    def static__baseSelect(self, qualified = None):
        """create a SELECT cols FROM table statement to be used by the
        selector functions (getSome, getUnique, joinTable)

        If qualified is some true value, get column names via call to
        getColumns with said qualified value.
        """
        sql = "SELECT " + string.join(self.getColumns(qualified), ', ')
        sql = sql + " FROM %s" % self.getTable()
        return sql

    def static__matchUnique(self, kw):
        """return a tuple of column names that will uniquely identify
        a row given the choices from kw"""
        for unique in self.unique:
            if type(unique) == types.StringType:
                if kw.has_key(unique) and kw[unique] is not None:
                    return (unique,)
            elif type(unique) == types.TupleType:
                for u in unique:
                    if not kw.has_key(u):
                        break
                else:
                    return unique

    def static__uniqueWhere(self, conn, kw):
        """given a connection and kw, using _matchUnique, generate a
        where clause to select a unique row.
        """
        unique = self._matchUnique(kw)
        if not unique:
            raise ValueError, 'No way to get unique row! %s %s' % (
                str(kw), unique)
        
        where = []
        values = []
        for u in unique:
            lit, val = conn.sqlStringAndValue(kw[u], u, self.fieldDict[u])
            where.append("%s = %s" % (u, lit))
            values.append(val)
        return string.join(where, ' AND '), values

    def static_getUnique(self, **kw):
        """given the attribute/value pairs in kw, retrieve a unique row
        and return a data class instance representing said row or None
        if no row was retrieved"""
        unique = self._matchUnique(kw)
        sql = self._baseSelect() + " WHERE "
        
        conn = self.getDBI()
        where, values = self._uniqueWhere(conn, kw)
        sql = sql + where
        results = conn.execute(sql, values, self.fieldDict)
        if len(results) > 1:
            raise PyDOError, 'got more than one row on unique query!'
        if not results:
            return
        if results:
            return self(results[0]) 

    def static_getSomeSQL(self, **kw):
        """given the attribute/value pairs in kw, return
        sql statement, values to be used in a call to conn.execute.
        If kw is empty, the WHERE text in the sql statement will still
        be preseverved.
        """
        sql = self._baseSelect() + " WHERE "
        conn = self.getDBI()
        where = []
        values = []
        for k, v in kw.items():
            notFlag = ''
            if isinstance(v, NOT):
                notFlag = '!'
                v = v.val
            lit, val = conn.sqlStringAndValue(v, k, self.fieldDict[k])
            
            where.append("%s %s= %s" % (
                k, notFlag, lit))
            values.append(val)
        whereClause = string.join(where, ' AND ')
        sql = sql + whereClause
        return sql, values
    
    def static_getSome(self, **kw):
        """given the attribute/value pairs in kw, return a (potentially
        empty) list of data class instances representing the rows that
        fulfill the constraints in kw"""
        sql, values = apply( self.getSomeSQL, (), kw)
        if not kw:
            sql = sql[:-7]
        conn = self.getDBI()
        results = conn.execute(sql, values, self.fieldDict)
        return map(self, results)

    def static_getSomeWhere(self, *args, **kw):
        andValues=list(args)
        for k, v in kw.items():
            andValues.append(operators.EQ(operators.FIELD(k), v))
        andlen=len(andValues)
        if andlen > 1:
            daOp=operators.AND(*andValues)
        elif andlen==1:
            daOp=andValues[0]
        else:
            daOp=None
        sql=(daOp and daOp.asSQL()) or ''
        return self.getSQLWhere(sql)

    def static_getTupleWhere(self, opTuple, **kw):
        if kw:
            _and=['AND', opTuple]
            for k, v in kw.items():
                _and.append(('=', FIELD(k), v))
            opTuple=tuple(_and)
        sql=operators.tupleToSQL(opTuple)
        return self.getSQLWhere(sql)

    def static_getSQLWhere(self, sql, values=()):
        base=self._baseSelect()
        if sql:
            sql="%s WHERE %s" % (base, sql)
        else:
            sql=base
        conn = self.getDBI()
        results = conn.execute(sql, values, self.fieldDict)
        return map(self, results)        
    
    def static_new(self, refetch = None, **kw):
        """create and return a new data class instance using the values in
        kw.  This will also affect an INSERT into the database.  If refetch
        is true, effectively do a getUnique on self.
        """
        if not self.mutable:
            raise ValueError, 'cannot make a new immutable object!'
        conn = self.getDBI()
        sql = "INSERT INTO %s " % self.getTable()
        self._validateFields(kw)
        extryKV = {}
        for s, sn in self.sequenced.items():
            if not kw.has_key(s):
                extryKV[s] = conn.getSequence(sn)

        kw.update(extryKV)

        cols = []
        values = []
        vals = []
        atts = []
        for k, v in kw.items():
            cols.append(k)
            field = self.fieldDict[k]
            atts.append(field)
            lit, val = conn.sqlStringAndValue(v, k, field)
            values.append(lit)
            vals.append(val)
        sql = sql + '(%s) VALUES ' % string.join(cols, ', ')
        sql = sql + '(%s)' % string.join(values, ', ')
        res = conn.execute(sql, vals, self.fieldDict)

        if len(self.auto_increment):
            for k, v in self.auto_increment.items():
                if not kw.has_key(k):
                    kw[k] = conn.getAutoIncrement(v)
                
        if res != 1:
            raise PyDOError, "inserted %s rows instead of 1" % res

        conn.postInsertUpdate(self, kw, 1)
        if not refetch:
            return self(kw)
        return apply(self.getUnique, (), kw)

    def static__validateFields(self, dict):
        """a simple field validator, basically checks to see that
        you don't try to set fields that don't exist."""
        for k in dict.keys():
            if not self.fieldDict.has_key(k):
                raise KeyError, 'object has no field %s' % k

    def static_scatterFetchSQL(self, objs):
        """do a scatter fetch (a select from more than one table) based
        on the relation information in objs which is of the form:
        [
           (object, attributes, destinationObject, destinationAttributes),
           (object, attributes, destinationObject, destinationAttributes)
        ]
        This basically states that objects attributes are a foreign key to
        destinationObject's destinationAttributes.

        For example, if you have User and UserResidence classes, a scatter
        fetch may be simply:
        userObj.scatterFetchSQL( [ (UserResidence, 'USER_OID', User, 'OID') ] )
        which if executed would return a list of tuples of:
            (userObj, userResObj)
        where userObj.['OID'] == userResObj['USER_OID']

        This function returns sql, baseColumnNames, and a modified version of
        the objs argument.
        """
        objs = ((self, None, None, None),) + tuple(objs)
        cols = []
        for obj in objs:
            cols.extend(obj[0].getColumns(1))
        tabs = map(lambda x:x[0].getTable(), objs)
        sql = "SELECT %s FROM %s WHERE " % (
            string.join(cols, ', '), string.join(tabs, ', '))
        j = []
        for obj, attr, dobj, dattr in objs:
            if type(attr) in (types.TupleType, types.ListType):
                if type(dattr) != type(attr):
                    raise TypeError, ("source and destination attributes for"
                                      " %s/%s aren't of same length") % (
                                          obj, dobj)
                
                for attri, dattri in map(None, attr, dattr):
                    j.append('%s.%s = %s.%s' % (obj.getTable(), attri,
                                                dobj.getTable(), dattri))

            else:
                if dobj:
                    j.append('%s.%s = %s.%s' % (obj.getTable(), attr,
                                                dobj.getTable(), dattr))
        sql = sql + string.join(j, ' AND ')
        return sql, cols, objs

    def static_scatterFetchPost(self, objs, sql, vals, cols):
        """handle the execution and processing of a scatter fetch to produce
        a result list -- returns the list of tuples referred to in the
        docstring of scatterFetchSQL"""
        conn = self.getDBI()
        results, fields = conn.execute(sql, vals, None)
        endResults = []

        sliceSets = []
        counter = 0 
        for obj in objs:
            cols = obj[0].getColumns()
            lenCols = len(cols)
            sliceSets.append([counter, counter+lenCols, obj[0]])
            counter = counter+lenCols

        resultSets = {}

        for result in results:
            counter = 0
            for set in sliceSets:
                if not resultSets.has_key(counter):
                    resultSets[counter] = []
                resultSets[counter].append(result[set[0]: set[1]])
                counter = counter + 1

        cvtedResultSets = {}
        for i in range(len(objs)):
            obj = objs[i][0]
            #print 'keys-->', resultSets.keys()
            r = map(obj, conn.convertResultRows(
                obj.getColumns(), obj.fieldDict, resultSets[i]))
            cvtedResultSets[i] = r

        result = []
        for i in range(len(cvtedResultSets[0])):
            l = []
            for j in range(len(cvtedResultSets)):
                l.append(cvtedResultSets[j][i])
            result.append(l)
        return result

    def static_scatterFetch(self, objs, **kw):
        """see scatterFetchSQL for format of objs and getSome for format
        of **kw
        """
        
        sql, cols, objs = self.scatterFetchSQL(objs)

        conn = self.getDBI()
        where = []
        values = []
        for k, v in kw.items():
            notFlag = ''
            if isinstance(v, NOT):
                notFlag = '!'
                v = v.val
            lit, val = conn.sqlStringAndValue(v, k, self.fieldDict[k])
            
            where.append("%s.%s %s= %s" % (
                self.getTable(), k, notFlag, lit))
            values.append(val)
        whereClause = string.join(where, ' AND ')
        if whereClause:
            sql = sql + " AND " + whereClause

        #make where clause here from **kw
        return self.scatterFetchPost(objs, sql, values, cols)

    ##############################
    ## PyDO instance methods
    ##############################
    #other pydo instance methods

    def updateValues(self, dict):
        """update self in database with the values in dict"""
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"
        sql = "UPDATE %s SET " % self.getTable()
        sets = []
        values = []
        conn = self.getDBI()
        atts = []
        
        for k, v in dict.items():
            field = self.fieldDict[k]
            #v =
            conn.typeCheckAndConvert(v, k, field)
            lit, val = conn.sqlStringAndValue(v, k, field)
            atts.append(field)
            values.append(val)
            sets.append("%s = %s" % (
                k, lit))
            
        where, wvalues = self._uniqueWhere(conn, self._dict)
        values = values + wvalues
        sql = sql + string.join(sets, ', ') + " WHERE " + where
        result = conn.execute(sql, values, self.fieldDict)
        if result > 1:
            raise PyDOError, "updated %s rows instead of 1" % result        
        conn.resetQuery()
        conn.postInsertUpdate(self, dict, 0)

    def delete(self):
        """remove the row that represents me in the database"""
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"
        conn = self.getDBI()
        unique, values = self._uniqueWhere(conn, self._dict)
        sql = 'DELETE FROM %s WHERE %s' % (self.getTable(), unique)
        conn.execute(sql, values, self.fieldDict)
        self.mutable = 0

    def refresh(self):
        """refetch myself from the database"""
        obj = apply(self.getUnique, (), self._dict)
        if not obj:
            raise ValueError, "current object doesn't exist in database!"
        mutable = self.mutable #save if was deleted, it still is deleted
        self._dict = obj._dict
        self.mutable = self._klass.mutable
            
    def joinTableSQL(self, thisAttrNames, pivotTable, thisSideColumns,
                     thatSideColumns, thatObject, thatAttrNames,
                     extraTables = []):
        """Handle many to many relations.  In short, do a

        SELECT thatObject.getColumns(1)
        FROM thatObject.getTable(), pivotTable
        WHERE pivotTable.thisSideColumn = self[myAttrName]
        AND pivotTable.thatSideColumn = thatObject.getTable().thatAttrName

        and return a list of thatObjects representing the resulting rows.
        """

        thisAttrNames = _tupleize(thisAttrNames)
        thisSideColumns = _tupleize(thisSideColumns)
        thatSideColumns = _tupleize(thatSideColumns)
        thatAttrNames = _tupleize(thatAttrNames)

        if len(thisSideColumns) != len(thisAttrNames):
            raise ValueError, ('thisSideColumns and thisAttrNames must '
                               'contain the same number of elements')
        if len(thatSideColumns) != len(thatAttrNames):
            raise ValueError, ('thatSideColumns and thatAttrNames must '
                               'contain the same number of elements')

        conn = self.getDBI()
        
        sql = thatObject._baseSelect(1) + ",%s WHERE " % string.join(
            [pivotTable] + extraTables, ', ')

        thisJoin = []
        vals = []

        for attr, col in map(None, thisAttrNames, thisSideColumns):
            lit, val = conn.sqlStringAndValue(
                self[attr], attr, self.fieldDict[attr])
            thisJoin.append('%s.%s = %s' % (pivotTable, col, lit))
            vals.append(val)

        sql = sql + string.join(thisJoin, ' AND ') + ' AND '

        thatJoin = []
        thatTable = thatObject.getTable()
        for attr, col in map(None, thatAttrNames, thatSideColumns):
            thatJoin.append('%s.%s = %s.%s' % (
                pivotTable, col, thatTable, attr))

        sql = sql + string.join(thatJoin, ' AND ')
        return sql, vals
        
        
    def joinTable(self, thisAttrNames, pivotTable, thisSideColumns,
                     thatSideColumns, thatObject, thatAttrNames):
        """see joinTableSQL for arguments

        This method executes the statement returned by joinTableSQL with
        the arguments and produces object from them.
        """
        conn = self.getDBI()
        sql, vals = self.joinTableSQL(thisAttrNames, pivotTable,
                                      thisSideColumns, thatSideColumns,
                                      thatObject, thatAttrNames)
        results = conn.execute(sql, vals, thatObject.fieldDict)
        return map(thatObject, results)        

    
def _tupleize(item):
    if type(item) == types.TupleType:
        return item
    return (item,)
