"""
my goals:

- no longer use the static module.

- it should be possible to easily associate other
  attributes with a field besides its type.

- it should work in multithreaded environments;
  review assumptions made about drivers.

- it should be possible to get a subclass of an object
  to have a subset of the full list of fields.

- automatically generate properties or other attribute-style access to
  fields; deal with anomalous cases in a non-showstopper manner,or make
  that interface optional on a per-class basis.  allow the name by which
  a field is referred to to be different from the real name of the field
  in the database (hence you can have database fields with names like
  'pass', 'class', etc.)

"""

from PyDBI import *
import operators

class _metapydo(type):
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
        #print "self in metaclass __init__: %s" % self
        
        for b in bases:
            try:
                b._classinit__()
            except AttributeError:
                pass
        try:
            self._classinit__()
        except AttributeError:
            pass
        
class _fieldproperty(object):
    def __init__(self, fieldname):
        self.__fieldname=fieldname

    def __get__(self, obj, type):
        return obj[self.__fieldname]

    def __set__(self, obj, value):
        return obj.update({self.__fieldname: value})
        

class _pydobase(object):
    __metaclass__=_metapydo
    
    mutable=0
    useAttrs=1
    connAlias=None
    unique=[]
    sequenced={}
    table=None
    extra_attrs=()
    fields=()
    auto_increment={}
    
    def class__classinit__(klass):
        scl=list(klass.__bases__)
        scl.reverse()
        klass.fieldAttrs=fieldAttrs={}
        attrs=('name', 'type') + klass.extra_attrs
        for b in scl:
            if hasattr(b, 'fieldAttrs'):
                fieldAttrs.update(b.fieldAttrs)
        for f in klass.fields:
            name=f[0]
            if isinstance(f[-1], dict):
                f=list(f)
                d1=f.pop()
            else:
                d1=None
            d=fieldAttrs[name]=dict(zip(attrs, f))
            d.setdefault('attrname', name)
            if d1:
                d.update(d1)
        klass.fieldDict=dict([(v['name'], v['type']) \
                              for v in fieldAttrs.itervalues()])
        klass.fields=tuple([tuple([fieldAttrs[n][a] for a in attrs]) \
                           for n in fieldAttrs.iterkeys()])

        if klass.useAttrs:
            for k, v in fieldAttrs.iteritems():
                attrname=v['attrname']
                if not hasattr(klass, attrname):
                    setattr(klass,
                            attrname,
                            _fieldproperty(k))

    def __init__(self, adict):
        self._dict=adict
        
    def class_getDBI(klass):
        "return the database interface"
        conn=DBIGetConnection(klass.connectionAlias)
        conn.resetQuery()
        return conn
    
    def class_commit(klass):
        return klass.getDBI().commit()

    def class_rollback(klass):
        return klass.getDBI().rollback()

    def __getitem__(self, item):
        return self._dict[item]

    def __setitem__(self, item, val):
        return self.update({item: val})

    def items(self):
        return self._dict.items()

    def has_key(self, key):
        return self._dict.has_key(key)

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def get(self, item, default=None):
        return self._dict.get(item, default)

    def update(self, adict):
        for k in adict:
            if not self.fieldAttrs.has_key(k):
                raise KeyError, "object %s has no field %s" \
                      % (self.__class__, k)
            self.updateValues(adict)
            self._dict.update(adict)

    def updateValues(self, adict):
        raise NotImplementedError, "no way to update"

    def dict(self):
        return self._dict.copy()

    def copy(self):
        return self.__class__(self._dict.copy())

    def __cachekey__(self):
        return self._dict

            
class PyDO(_pydobase):
    
    def class_getColumns(klass, qualified=None):
        if not qualified:
            return klass.fieldAttrs.keys()
        return ['%s.%s' % (klass.table, x) for x in klass.fieldAttrs.iterkeys()]

    def class_getTable(klass):
        return klass.table

    def class__baseSelect(klass, qualified=None):
        sql='SELECT %s FROM %s' % (', '.join(klass.getColumns(qualified)),
                                   klass.table)
        return sql

    def class__matchUnique(klass, kw):
        """return a tuple of column names that will uniquely identify
        a row given the choices from kw"""
        for unique in klass.unique:
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
            lit, val = conn.sqlStringAndValue(kw[u], u, klass.fieldAttrs[u]['type'])
            where.append("%s = %s" % (u, lit))
            values.append(val)
        return ' AND '.join(where), values

    def class_getUnique(klass, **kw):
        """given the attribute/value pairs in kw, retrieve a unique row
        and return a data class instance representing said row or None
        if no row was retrieved"""
        unique = klass._matchUnique(kw)
        sql = klass._baseSelect() + " WHERE "
        
        conn = klass.getDBI()
        where, values = klass._uniqueWhere(conn, kw)
        sql = sql + where
        results = conn.execute(sql, values, klass.fieldDict)
        if not results:
            return
        if len(results) > 1:
            raise PyDOError, 'got more than one row on unique query!'
        if results:
            return klass(results[0]) 

    def class_getSomeSQL(klass, **kw):
        """given the attribute/value pairs in kw, return
        sql statement, values to be used in a call to conn.execute.
        If kw is empty, the WHERE text in the sql statement will still
        be preseverved.
        """
        sql = klass._baseSelect() + " WHERE "
        conn = klass.getDBI()
        where = []
        values = []
        for k, v in kw.items():
            lit, val = conn.sqlStringAndValue(v, k, klass.fieldDict[k])
            
            where.append("%s=%s" % (
                k, lit))
            values.append(val)
        sql = sql + ' AND '.join(where)
        return sql, values
    
    def class_getSome(klass, **kw):
        """given the attribute/value pairs in kw, return a (potentially
        empty) list of data class instances representing the rows that
        fulfill the constraints in kw"""
        sql, values=klass.getSomeSQL(**kw)
        if not kw:
            sql=sql[:-7]
        conn=klass.getDBI()
        results = conn.execute(sql, values, klass.fieldDict)
        if type(results)==types.ListType:
            return map(klass, results)
        else:
            return []

    def class_getSomeWhere(klass, *args, **kw):
        """
        
        """
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
        return klass.getSQLWhere(sql)

    def class_getTupleWhere(klass, opTuple, **kw):
        if kw:
            _and=opTuple and ['AND', opTuple] or []
            for k, v in kw.items():
                _and.append(('=', FIELD(k), v))
            opTuple=tuple(_and)
        sql=opTuple and operators.tupleToSQL(opTuple) or ''
        return klass.getSQLWhere(sql)

    def class_getSQLWhere(klass, sql, values=()):
        base=klass._baseSelect()
        if sql:
            sql="%s WHERE %s" % (base, sql)
        else:
            sql=base
        conn = klass.getDBI()
        results = conn.execute(sql, values, klass.fieldDict)
        if results and type(results)==types.ListType:
            return map(klass, results)
        else:
            return []
    
    def class_new(klass, refetch = None, **kw):
        """create and return a new data class instance using the values in
        kw.  This will also affect an INSERT into the database.  If refetch
        is true, effectively do a getUnique on klass.
        """
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
            field = klass.fieldDict[k]
            atts.append(field)
            lit, val = conn.sqlStringAndValue(v, k, field)
            values.append(lit)
            vals.append(val)
        sql = sql + '(%s) VALUES ' % string.join(cols, ', ')
        sql = sql + '(%s)' % string.join(values, ', ')
        res = conn.execute(sql, vals, klass.fieldDict)

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

    def class__validateFields(klass, dict):
        """a simple field validator, basically checks to see that
        you don't try to set fields that don't exist."""
        for k in dict.keys():
            if not klass.fieldDict.has_key(k):
                raise KeyError, 'object has no field %s' % k

    def class_scatterFetchSQL(klass, objs):
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
        objs = ((klass, None, None, None),) + tuple(objs)
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
            #print 'keys-->', resultSets.keys()
            r = map(obj, conn.convertResultRows(obj.getColumns(),
                                                obj.fieldDict,
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
            lit, val = conn.sqlStringAndValue(v, k, klass.fieldDict[k])
            
            where.append("%s.%s %s= %s" % (
                klass.getTable(), k, notFlag, lit))
            values.append(val)
        whereClause = ' AND '.join(where)
        if whereClause:
            sql = sql + " AND " + whereClause

        #make where clause here from **kw
        return klass.scatterFetchPost(objs, sql, values, cols)

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



##DBIInitAlias('cms', 'pydo:postgresql:localhost:cms:cmsicle:whatever:verbose')
##class Channels(PyDO):
##    table='channels'
##    fields=(
##        ('id', 'integer', {'foo' : 'balaban', 'nougat' : 'frosty'}),
##        ('title', 'text'),
##        ('nickname', 'text'))
##    mutable=1
##    connectionAlias='cms'
##    sequenced={'id' : 'channels_id_seq'}
##    unique=['id']
