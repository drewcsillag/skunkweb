#  
#  Copyright (C) 2001-2003 Andrew T. Csillag <drew_csillag@geocities.com>,
#                          Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#
# This is a modified version of PyDO.
# See bottom of file for changelog and motivation.

from PyDBI import *
import operators
import types, string

class _fieldproperty(object):
    def __init__(self, fieldname):
        self.__fieldname=fieldname

    def __get__(self, obj, type):
        return obj[self.__fieldname]

    def __set__(self, obj, value):
        return obj.update({self.__fieldname: value})

class _metapydo(type):
    """ Meta-class for _pydobase
    """
    def __new__(self, cl_name, bases, namespace):
        prefix_descriptor_pairs=(('static_', staticmethod),
                                 ('class_', classmethod))
        for k, v in namespace.iteritems():
            for prefix, descriptor in prefix_descriptor_pairs:
                lenpre=len(prefix)
                if k.startswith(prefix):
                    methname=k[lenpre:]
                    if methname in namespace.iterkeys():
                        raise ValueError, \
                              "duplicate method name: %s" % methname
                    namespace[methname]=descriptor(v)
                    del namespace[k]
        if '__class_new__' in namespace:
            res=namespace['__class_new__'](self, cl_name, bases, namespace)
            if res is not None:
                return res
        return type.__new__(self, cl_name, bases, namespace)
    
    def __init__(self, cl_name, bases, namespace):      
        for b in bases:
            try:
                b._classinit__()
            except AttributeError:
                pass
        try:
            self._classinit__()
        except AttributeError:
            pass


class _pydobase(object):
    """ Baseclass for PyDO
    
    _pydobase implements most of the generic
    functionality to make persistent PyDO-instances behave
    like normal Python classes/object.
    
    Not meant to be uses directly. Inherit from PyDO instead.
    """
    __metaclass__=_metapydo
    
    mutable=1
    useAttrs=1
    connAlias=None
    unique=[]
    sequenced={}
    table=None
    fields=()
    dbColumns={}
    auto_increment={}
    _unique = []
    _dict={}
    
    def class__classinit__(klass):
        """ Initializes a PyDO-class definition
        
        Do not use directly. This method cannot be
        overridden.
        """
        # do inheritance ...
        scl=list(klass.__bases__)
        # --------------------------------------------------------
        # scl.reverse()
        # In old-style PyDO we needed to reverse the scl because
        # because of static (?). Now it just messes up mro.
        # Just don't reverse the scl and mro is ok.
        # --------------------------------------------------------
        
        # ---------------------------------------------------------
        # Note that we need to blank out the attributes before
        # inheritance, otherwise we'll inherit from our siblings
        # as well.
        # ---------------------------------------------------------
        klass.fieldDict=fieldDict={}
        klass._dict = {}
        un = klass._unique
        klass._unique = []
        klass.sequenced={}
        
        for b in scl:
            if hasattr(b, 'fieldDict'):
                fieldDict.update(b.fieldDict)
            if b.connAlias:
                klass.connAlias = b.connAlias
            klass._unique.extend(b._unique)
            klass.sequenced.update(b.sequenced)
            klass.auto_increment.update(b.auto_increment)
        
        for f in klass.fields:
            if len(f) == 2:
                # must be either old-style field def,
                # or new-style class-based
                (n, v) = f
                if type(v) is types.StringType:
                    # old style field def
                    # v is a string, must be db-type
                    fieldDict[n] = {
                        'dbType': v,
                        'dbName': n
                        }
                    x = {}
                else:
                    # new style, class-based field def
                    # must be a dict-like class or a real dict
                    # with at least a 'dbName' field.
                    fieldDict[n] = {}
                    if v.has_key('dbName'):
                        fieldDict[n]['dbName'] = v['dbName']
                    else:
                        fieldDict[n]['dbName'] = n
                    x = v
            elif len(f) == 3:
                # must be old-style with extra info
                (n, v, x) = f
                fieldDict[n] = {
                    'dbName': n,
                    'dbType': v
                    }
            else:
                raise TypeError
            
            # get extra options from 'x'
            # supported options:
            # - optUnique: boolean
            # - optSequenced: name of sequencer
            # - optAutoIncrement: boolean
            # - optPrimaryKey: boolean (implies optUnique)
            # all options are stored in fieldDict[fieldname]
            dbName = fieldDict[n]['dbName']
            for (attrKey, attrValue) in x.iteritems():
                fieldDict[n][attrKey] = attrValue
                if attrKey == 'optUnique' or attrKey == 'optPrimaryKey':
                    klass._unique.append(dbName)
                if attrKey == 'optSequenced':
                    klass.sequenced.update({dbName: attrValue})
                if attrKey == 'optAutoIncrement':
                    klass.auto_increment.update({dbName: attrValue})
        klass._unique.extend(klass.unique)
        klass.dbColumns = {}
        for field, attr in klass.fieldDict.iteritems():
            klass.dbColumns[attr['dbName']] = attr['dbType']
            if klass.useAttrs and not hasattr(klass, field):
	        setattr(klass, field, _fieldproperty(field))
    
   
    def __init__(self, adict):
        self._dict=adict
    
    def class_getDBI(klass):
        """return the database interface
        """
        conn=DBIGetConnection(klass.connectionAlias)
        conn.resetQuery()
        return conn
    
    def class_commit(klass):
        """ Commit changes to database
        """
        return klass.getDBI().commit()
    
    def class_rollback(klass):
        """ Rollback current transaction
        """
        return klass.getDBI().rollback()
    
    def __getitem__(self, item):
        """ Part of dictionary interface for field access
        """
        return self._dict[self.fieldDict[item]['dbName']]
    
    def __setitem__(self, item, val):
        """ Part of dictionary interface for field access
        """
        return self.update({item: val})
    
    def items(self):
        """ Part of dictionary interface for field access
        """             
        return self._dict.items()
    
    def has_key(self, key):
        """ Part of dictionary interface for field access
        """                             
        key = self.fieldDict[key]['dbName']
        return self._dict.has_key(key)
    
    def keys(self):
        """ Part of dictionary interface for field access
        """                                             
        return self.fieldDict.keys()
    
    def values(self):
        """ Part of dictionary interface for field access
        """                                             
        return self._dict.values()
    
    def get(self, item, default=None):
        """ Part of dictionary interface for field access
        """                             
        key = self.fieldDict[item]['dbName']
        return self._dict.get(key, default)
    
    def update(self, adict):
        """ Part of dictionary interface for field access
        """                             
        #print "Update is called with: %s" % adict
        bdict = {}
        for k in adict:
            try:
                bdict[self.fieldDict[k]['dbName']] = adict[k]
            except KeyError:
                raise KeyError, "object %s has no field %s" \
                      % (self.__class__, k)
            self.updateValues(adict)
            self._dict.update(bdict)
    
    def updateValues(self, adict):
        """ Updates underlying database table
        
        Called whenever fields are updated.
        
        If you want to have some fields changed
        automatically on update (e.g. a 'lastmodified'
        timestamp), you can do that by overriding this
        method.
        
        Don't forget to call the parents updateValues
        when you're done, or nothing gets updated
        at all!
        
        """
        raise NotImplementedError, "no way to update"
    
    def dict(self):
        """ Returns a dictionary containing of all fields
        """
        return self._dict.copy()
    
    def copy(self):
        """  Part of dictionary interface for field access
        """     
        return self.__class__(self._dict.copy())
    
    def __cachekey__(self):
        """ Return a key to be used by skunkwebs caching mechanism.
        
        Skunkweb allows for caching components. Arguments to
        cached components must be hashable or (in case of
        classes you write yourself) implement a __cachekey__
        method that returns something which can be used
        to uniquely identify it.
        
        Default is to return a dict representation of the
        instance.
        
        If you plan on using a particular class in combination
        with cached components, it is probably a wise thing to
        include a 'lastmodified' field that is automatically
        updated everytime the object changes (by overriding
        updateValues).
        
        This is because when the called component changes
        the object, you will find that it changes only the first time
        the component is called, becuase on subequent calls, the output
        is cached and the component will not be executed.
        """
        return self._dict


class PyDO(_pydobase):
    
    ####################################################
    ##
    ## Public interface starts here
    ##
    ##
    ## Class methods
    ##
    def class_new(klass, refetch = None, **kw):
        """create and return a new data class instance using the values in
        kw.  This will also affect an INSERT into the database.  If refetch
        is true, effectively do a getUnique on klass.
        """
        kw = klass._convertKW(kw)
        if not klass.mutable:
            raise ValueError, 'cannot make a new immutable object!'
        conn = klass.getDBI()
        sql = "INSERT INTO %s " % klass.getTable()
        klass._validateFields(kw)
        extryKV = {}
        for s, sn in klass.sequenced.items():
            if not kw.has_key(s):
                extryKV[s] = conn.getSequence(sn)
        
        kw.update(extryKV)
        
        cols = []
        values = []
        vals = []
        atts = []
        for k, v in kw.items():
            cols.append(k)
            field = klass.dbColumns[k]
            atts.append(field)
            lit, val = conn.sqlStringAndValue(v, k, field)
            values.append(lit)
            vals.append(val)
        sql = sql + '(%s) VALUES ' % ', '.join(cols)
        sql = sql + '(%s)' % ', '.join(values)
        res = conn.execute(sql, vals, klass.dbColumns)
        
        if len(klass.auto_increment):
            for k, v in klass.auto_increment.items():
                if not kw.has_key(k):
                    kw[k] = conn.getAutoIncrement(v)
        
        if res != 1:
            raise PyDOError, "inserted %s rows instead of 1" % res
        
        conn.postInsertUpdate(klass, kw, 1)
        if not refetch:
            return klass(kw)
        return apply(klass.getUnique, (), kw)
    
    def class_getColumns(klass, qualified=None):
        """ Return a list of all columns in this table.
        
        If qualified is True, return fully qualified columnnames
        (i.e. table.column)
        """
        if not qualified:
            return klass.dbColumns.keys()
        return ['%s.%s' % (klass.table, x) for x in klass.dbColumns.iterkeys()]
    
    def class_getTable(klass):
        """ Return the name of the underlying database table
        """
        return klass.table
    
    def class_getUnique(klass, **kw):
        """ Retrieve one particular instance of this class.
        
        Given the attribute/value pairs in kw, retrieve a unique row
        and return a data class instance representing said row or None
        if no row was retrieved.
            """
        kw = klass._convertKW(kw)
        
        unique = klass._matchUnique(kw)
        sql = klass._baseSelect() + " WHERE "
        
        conn = klass.getDBI()
        where, values = klass._uniqueWhere(conn, kw)
        sql = sql + where
        results = conn.execute(sql, values, klass.dbColumns)
        if not results:
            return
        if len(results) > 1:
            raise PyDOError, 'got more than one row on unique query!'
        if results:
            return klass(results[0]) 
            
            
    def class__orderByString(self, order_by):
        
        order_list = []
        
        for item in order_by:
            if type(item) == types.StringType:
                order_list.append(item)
            else:
                order_list.append(string.join(item, ' '))
                    
        sql = ' ORDER BY %s' % string.join(order_list, ', ')
        
        return sql
    
    def class_getSomeSQL(klass, **kw):
        """ Prepare the SQL required to retrieve some objects by keyword.
        
        Given the attribute/value pairs in kw, return
        sql statement, values to be used in a call to conn.execute.
        If kw is empty, the WHERE text in the sql statement will still
        be preseverved.
        """
        kw = klass._convertKW(kw)
        sql = klass._baseSelect() + " WHERE "
        conn = klass.getDBI()
        where = []
        values = []
        order = []
        limit = 0
        offset = 0
        key_count = 0
        for k, v in kw.items():
            if k == 'order':
                if type(v) == types.StringType:
                    order.append(v)
                else:
                    order.extend(v)
                continue
            elif k == 'limit':
                limit = v
                continue
            elif k == 'offset':
                offset = v
                continue
            else:
                key_count += 1
            lit, val = conn.sqlStringAndValue(v, k, klass.dbColumns[k])
            
            where.append("%s=%s" % (
            k, lit))
            values.append(val)
        
        if key_count != 0:
            sql = sql + ' AND '.join(where)
        else:
            sql = sql[:-7]
                
        if len(order):
            sql += klass._orderByString(order)
        
        if limit:
            sql = sql + ' LIMIT %d' % limit
            
        if offset:
            sql = sql + ' OFFSET %d' % offset 
            
        return sql, values
    
    def class_getSome(klass, **kw):
        """ Retrieve some objects by keyword
        
        Given the attribute/value pairs in kw, return a (potentially
        empty) list of data class instances representing the rows that
        fulfill the constraints in kw
        """
        kw = klass._convertKW(kw)
        sql, values=klass.getSomeSQL(**kw)
        conn=klass.getDBI()
        results = conn.execute(sql, values, klass.dbColumns)
        if type(results)==types.ListType:
            return map(klass, results)
        else:
            return []
    
    def class_getSomeWhere(klass, *args, **kw):
        """ Retrieve some objects of this particular class.
        
        Allows you to use the operator objects in PyDO.operators to be
        able to use sql operators other than the implicit AND as
        used by the other static get methods.
        
        The **kw argument is the same as the other static get methods.
        The *args argument however allows you to combine operators to
        do operations like OR, NOT, LIKE, etc. For example, the following
        would get all rows where the last name field was LIKE Ingers%.
        
        obj.getSomeWhere(LIKE(FIELD('last_name'), ('Ingers%')))
        
        """
        kw = klass._convertKW(kw)
        andValues=list(args)
        for k, v in kw.items():
            if k not in ('order', 'offset', 'limit'):
                andValues.append(operators.EQ(operators.FIELD(k), v))
        andlen=len(andValues)
        if andlen > 1:
            daOp=operators.AND(*andValues)
        elif andlen==1:
            daOp=andValues[0]
        else:
            daOp=None
        sql=(daOp and daOp.asSQL()) or ''
        
        order=[]
        limit=0
        offset=0
        if kw.get('order'):
            if type(kw['order']) == types.StringType:
                order.append(kw['order'])
            else:
                order.extend(kw['order'])
        if kw.get('limit'):
            limit = kw['limit']
        if kw.get('offset'):
            offset = kw['offset']
        
        return klass.getSQLWhere(sql, order=order, limit=limit, offset=offset)
    
    def class_getTupleWhere(klass, opTuple, order=(), limit=0, offset=0, **kw):
        """ Retrieve objects using Lisp-like queries
        
        Allows you to use a somewhat Lispish notation for generating
        SQL queries, like so:
        
        obj.getTupleWhere(('OR', 
        ('LIKE', FIELD('last_name'), 'Ingers%'), 
        ('OR', ('<>', FIELD('id'), 355),
        ('=', FIELD('id'), 356))))
        
        Strings are used to represent operators rather than the SQLOperator
        class wrappers used in getSomeWhere(), but the FIELD and SET classes
        are still useful. The kw argument is treated the same as in
        getSome() and getSomeWhere().
        
        """
        kw = klass._convertKW(kw)
        
        if kw:
            _and=opTuple and ['AND', opTuple] or []
            for k, v in kw.items():
                _and.append(('=', FIELD(k), v))
            opTuple=tuple(_and)
        sql=opTuple and operators.tupleToSQL(opTuple) or ''
        
        order_list=[]

        if order:
            if type(order) == types.StringType:
                order_list.append(order)
            else:
                order_list.extend(order)        
        
        return klass.getSQLWhere(sql, order=order_list, limit=limit, offset=offset)
    
    def class_getSQLWhere(klass, sql, values=(), order=(), limit=0, offset=0):
        """ Retrieve objects with custom 'where' clause.
        
        Executes a sql statement to fetch the object type where
        you supply the where clause (without the WHERE keyword) and
        values in the case that you bind variables.
        """
        base=klass._baseSelect()
        if sql:
            sql="%s WHERE %s" % (base, sql)
        else:
            sql=base

        if len(order):
            sql += klass._orderByString(order)
        if limit:
            sql += ' LIMIT %d' % limit
        if offset:
            sql += ' OFFSET %d' % offset

        conn = klass.getDBI()
        results = conn.execute(sql, values, klass.dbColumns)
        if results and type(results)==types.ListType:
            return map(klass, results)
        else:
            return []
    
    def class_scatterFetchSQL(klass, objs):
        """ Select objects from multiple tables
        
        Do a scatter fetch (a select from more than one table) based
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
        objs = ((klass, None, None, None),) + tuple(objs)
        cols = []
        for obj in objs:
            cols.extend(obj[0].getColumns(1))
        tabs = map(lambda x:x[0].getTable(), objs)
        sql = "SELECT %s FROM %s WHERE " % (', '.join(cols),
                                            ', '.join(tabs))
        j = []
        for obj, attr, dobj, dattr in objs:
            if type(attr) in (types.TupleType, types.ListType):
                if type(dattr) != type(attr):
                    raise TypeError, ("source and destination attributes for"
                    " %s/%s aren't of same length") % (
                    obj, dobj)
                
                for attri, dattri in map(None, attr, dattr):
                    j.append('%s.%s = %s.%s' % (obj.getTable(), klass.fieldDict[attri]['dbName'],
                    dobj.getTable(), klass.fieldDict[dattri]['dbName']))
                
            else:
                if dobj:
                    j.append('%s.%s = %s.%s' % (obj.getTable(), klass.fieldDict[attr]['dbName'],
                    dobj.getTable(), klass.fieldDict[dattr]['dbName']))
        sql = sql + ' AND '.join(j)
        return sql, cols, objs
    
    def class_scatterFetchPost(klass, objs, sql, vals, cols):
        """handle the execution and processing of a scatter fetch to produce
        a result list -- returns the list of tuples referred to in the
        docstring of scatterFetchSQL"""
        conn = klass.getDBI()
        results, fields = conn.execute(sql, vals, None)
        if not results:
            return []
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
            r = map(obj, conn.convertResultRows(obj.getColumns(),
            obj.dbColumns,
            resultSets[i]))
            cvtedResultSets[i] = r
        
        result = []
        for i in range(len(cvtedResultSets[0])):
            l = []
            for j in range(len(cvtedResultSets)):
                l.append(cvtedResultSets[j][i])
            result.append(l)
        return result
    
    def class_scatterFetch(klass, objs, **kw):
        """see scatterFetchSQL for format of objs and getSome for format
        of **kw
        """
        
        sql, cols, objs = klass.scatterFetchSQL(objs)
        
        conn = klass.getDBI()
        where = []
        values = []
        for k, v in kw.items():
            notFlag = ''
            if isinstance(v, NOT):
                notFlag = '!'
                v = v.val
            lit, val = conn.sqlStringAndValue(v, k, klass.dbColumns[k])
            
            where.append("%s.%s %s= %s" % (
            klass.getTable(), k, notFlag, lit))
            values.append(val)
        whereClause = ' AND '.join(where)
        if whereClause:
            sql = sql + " AND " + whereClause
        
        #make where clause here from **kw
        return klass.scatterFetchPost(objs, sql, values, cols)
    
    ##############################
    ## Public instance methods
    ##############################
    
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
            fieldName = self.fieldDict[k]['dbName']
            fieldType = self.fieldDict[k]['dbType']
            conn.typeCheckAndConvert(v, fieldName, fieldType)
            lit, val = conn.sqlStringAndValue(v, fieldName, fieldType)
            atts.append(fieldType)
            values.append(val)
            sets.append("%s = %s" % (fieldName, lit))
        
        where, wvalues = self._uniqueWhere(conn, self._dict)
        values = values + wvalues
        sql = '%s%s WHERE %s' % (sql, ', '.join(sets), where)
        result = conn.execute(sql, values, self.dbColumns)
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
        conn.execute(sql, values, self.dbColumns)
        self.mutable = 0
    
    def refresh(self):
        """refetch myself from the database"""
        obj = apply(self.getUnique, (), self._dict)
        if not obj:
            raise ValueError, "current object doesn't exist in database!"
        #        mutable = self.mutable #save if was deleted, it still is deleted
        self._dict = obj._dict
    #        self.mutable = self._klass.mutable
    
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
        
        thisAttrNames = self._convertTupleKW(_tupleize(thisAttrNames))
        thisSideColumns = _tupleize(thisSideColumns)
        thatSideColumns = _tupleize(thatSideColumns)
        thatAttrNames = self._convertTupleKW(_tupleize(thatAttrNames))
        
        if len(thisSideColumns) != len(thisAttrNames):
            raise ValueError, ('thisSideColumns and thisAttrNames must '
            'contain the same number of elements')
        if len(thatSideColumns) != len(thatAttrNames):
            raise ValueError, ('thatSideColumns and thatAttrNames must '
            'contain the same number of elements')
        
        conn = self.getDBI()
        
        sql = '%s,%s WHERE ' % (thatObject._baseSelect(1),
                                ', '.join([pivotTable]+extraTables))
        
        thisJoin = []
        vals = []
        
        for attr, col in map(None, thisAttrNames, thisSideColumns):
            lit, val = conn.sqlStringAndValue(
            self[attr], attr, self.dbColumns[attr])
            thisJoin.append('%s.%s = %s' % (pivotTable, col, lit))
            vals.append(val)
        
        sql = '%s%s AND ' % (sql, ' AND '.join(thisJoin))
        
        thatJoin = []
        thatTable = thatObject.getTable()
        for attr, col in map(None, thatAttrNames, thatSideColumns):
            thatJoin.append('%s.%s = %s.%s' % (pivotTable,
                                               col,
                                               thatTable,
                                               attr))
        
        sql = '%s%s' % (sql, ' AND '.join(thatJoin))
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
        results = conn.execute(sql, vals, thatObject.dbColumns)
        return map(thatObject, results)        
    
    
    ####################################################
    ##
    ## Private methods start here
    ##
    ## Following methods are not part of the public
    ## interface.
    ##
    ##
    def class__validateFields(klass, dict):
        """a simple field validator, basically checks to see that
        you don't try to set fields that don't exist."""
        for k in dict.keys():
            if not klass.fieldDict.has_key(k):
                raise KeyError, 'object has no field %s' % k
    
    def class__baseSelect(klass, qualified=None):
        sql='SELECT %s FROM %s' % (', '.join(klass.getColumns(qualified)),
        klass.table)
        return sql
    
    def class__matchUnique(klass, kw):
        """return a tuple of column names that will uniquely identify
        a row given the choices from kw"""
        for unique in klass._unique:
            if isinstance(unique, str):
                if kw.has_key(unique) and kw[unique] is not None:
                    return (unique,)
            elif isinstance(unique, tuple):
                for u in unique:
                    if not kw.has_key(u):
                        break
                else:
                    return unique
    
    def class__uniqueWhere(klass, conn, kw):
        """given a connection and kw, using _matchUnique, generate a
        where clause to select a unique row.
        """
        unique = klass._matchUnique(kw)
        if not unique:
            raise ValueError, 'No way to get unique row! %s %s' % (
            str(kw), unique)
        
        where = []
        values = []
        for u in unique:
            lit, val = conn.sqlStringAndValue(kw[u], u, klass.dbColumns[u])
            where.append("%s = %s" % (u, lit))
            values.append(val)
        return ' AND '.join(where), values
    
    # following two methods are helper functions to convert
    # either a dict or a tuple containing Python attribute names
    # into their corresponding database column names. This is
    # to allow a difference between attribute name and column
    # name without putting the burden of conversion on the
    # developer.
    
    # for tuples, used in scatterFetch etc.
    def class__convertTupleKW(klass, tup):
        nt = []
        for i in tup:
            try:
                nt.append(klass.fieldDict[i]['dbName'])
            except KeyError:
                # apparently already converted
                # or just bogus. Neither way should we
                # worry about it here. Return original
                # input and let it (perhaps) go wrong
                # somewhere else.
                return tup
        return tuple(nt)
    
    # for dicts, used in getSome, getUnique etc.
    def class__convertKW(klass, kw):
        nkw = {}
        for k, v in kw.iteritems():
            try:
                nkw[klass.fieldDict[k]['dbName']] = v
            except KeyError:
                # apparently already converted
                # or just bogus. Neither way should we
                # worry about it here. Return original
                # input and let it (perhaps) go wrong
                # somewhere else. 
                return kw
        return nkw


def _tupleize(item):
    if type(item) == types.TupleType:
        return item
    return (item,)



# 2003-10-20 
#   Brian Olsen <brian@qinternet.com>
#
# Added the offset, limit, and order parameters to getSome(), getSomeSQL()
# getTupleWhere(), getSomeWhere(), and getSQLWhere(). A PyDO statement like
# this:
#
# MyTable.getSome(id=1, order=('id',), limit=1, offset=2)
#
# will produce something like this:
#
# SELECT id FROM my_table WHERE id=1 ORDER BY id LIMIT 1 OFFSET 2
#
# 2003-08-24 several modifications by:
#   Jacob Smullyan <smulloni@smullyan.org>
#   Jeroen van Dongen <jeroen@vthings.net>
#
# Following modifications are made in an effort to
# make PyDO's more like regular Python classes:
#
# - The static module is no longer used. PyDO classes are now
#   regular Python classes.
# - mro matches the mro for Python new-style classes
#   So diamond-shaped class hierarchies are possible (although
#   I'm not sure how to reflect that in SQL, but that's your
#   problem :-). 
# - Fields can be accessed either dictionary-style or
#   attribute-style
# - The name of the field in the database may differ from the
#   Python attribute name (hence you can have database fields with names like
#   'pass', 'class', etc.)
# - It is now possible to associate other attributes with a
#   a field, besides its database-type
#
# The following modifications are still on the wishlist:
# - it should work in multithreaded environments;
#   review assumptions made about drivers.
#   [JvD: probably best is to just use a multithread-aware driver, such
#    as Psycopg?]
# - it should be possible to get a subclass of an object
#   to have a subset of the full list of fields.
#   [JvD: perhaps drop requirement? Or create a method which fetches
#    only a few attributes, based on a getUnique?]
#

