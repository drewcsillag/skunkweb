#!/usr/local/bin/python
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import cStringIO
import sys
import operator
import sapdbapi
import string

#constraint types:
# P: primary key
# R: foriegn key to primary key
# C: check constraint (e.g. NOT NULL)
# U: unique
class Constraint:
    def __init__(self, name, kind, table, references, searchCondition):
        self.name = name
        self.kind = kind
        self.table = table
        self.references = references
        self.columns = []
        self.searchCondition = searchCondition

    def __str__(self):
        if self.kind == 'U':
            return "<Unique Constraint %s columns: %s>" % (
                self.name,
                string.join(map(lambda x:x.column, self.columns), ', '))
        elif self.kind == 'C':
            return "<Check constraint: %s %s>" % (self.name,
                                                  self.searchCondition)
        elif self.kind == 'P':
            return '<Primary key: %s columns: %s>' % (
                self.name,
                string.join(map(lambda x:x.column, self.columns), ', '))
        elif self.kind == 'R':
            # ref = constraints[self.references]
            #return ('<Foreign key: %s columns: %s references table:'
            #        ' %s columns: %s>') % (
            #    self.name,
            #    string.join(map(lambda x:x.column, self.columns), ', '),
            #    ref.table,
            #    string.join(map(lambda x:x.column, ref.columns), ', '))
	    return '<Foreign key: %s>' % self.name
        
        
class ConstraintColumn:
    def __init__(self, name, table, column):
        self.name = name
        self.table = table
        self.column = column

class ForeignKey:
    def __init__(self, table, column, reftable, refcolumn):
        self.table = table
	self.column = column
        self.reftable = reftable
        self.refcolumn = refcolumn

class Relation:
    def __init__(self, myAttrs, theirTable, theirAttrs):
        self.myAttrs = myAttrs
        self.theirTable = theirTable
        self.theirAttrs = theirAttrs

class OneToOne(Relation): pass
class OneToMany(Relation): pass
class ManyToOne(Relation): pass
class ManyToMany(Relation):
    def __init__(self, myAttrs, joinTable, mySideJoinAttrs,
                 theirSideJoinAttrs, theirTable, theirAttrs, methName=None):
        self.methName = methName
        self.myAttrs = myAttrs
        self.joinTable = joinTable
        self.mySideJoinAttrs = mySideJoinAttrs
        self.theirSideJoinAttrs = theirSideJoinAttrs
        self.theirTable = theirTable
        self.theirAttrs = theirAttrs
        
def getObjects(conn, user):
    #get TABLEs, SEQUENCEs and INDEXes (perhaps packages too?)
    cur = conn.cursor()
    cur.execute('SELECT OBJECT_NAME, OBJECT_TYPE FROM ALL_OBJECTS WHERE '
                'OWNER=:p1', (user,))
    return cur.fetchall()

def descTable(conn, user, table):
    #get columns and datatypes for a table
    cur = conn.cursor()
    cur.execute('SELECT COLUMN_NAME, DATA_TYPE FROM ALL_TAB_COLUMNS WHERE '
                'TABLE_NAME=:p1 AND OWNER=:p2', (table, user))
    return cur.fetchall()

def getConstraints(conn, user):
    #Get constraints for user
    cur = conn.cursor()
    cur.execute('select CONSTRAINT_NAME, CONSTRAINT_TYPE, TABLE_NAME, '
                'R_CONSTRAINT_NAME, SEARCH_CONDITION from all_constraints '
                'where owner=:p1',
                (user,))
    d = {}
    map(lambda r, d=d: operator.__setitem__(d, r[0], apply(Constraint, r)), cur.fetchall())
    d['NOT NULL'] = Constraint('NOT NULL', 'C', '', '', None)
    return d

def getColumnConstraints(conn, user):
    #which columns do said constraints belong to
    cur = conn.cursor()
    cur.execute("SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME from SYS.ALL_CONS_COLUMNS WHERE "
                "OWNER=:p1", (user,))
    r = cur.fetchall()

    return map(lambda x: apply(ConstraintColumn, x), r)

def getForeignKeyColumns(conn, user):
    #which columns do said constraints belong to
    cur = conn.cursor()
    cur.execute("SELECT TABLENAME,COLUMNNAME,REFTABLENAME,REFCOLUMNNAME from DOMAIN.FOREIGNKEYCOLUMNS WHERE "
                "OWNER=:p1", (user,))
    r = cur.fetchall()

    return map(lambda x: apply(ForeignKey, x), r)

def dictify(res, tbldesc):
    r = []
    for re in res:
        d = {}
        for i, j in map(None, re, tbldesc):
            print i, j
            d[j[0]] = i
        r.append(d)
    return r

def printDict(x):
    for i in x.items():
        print "%s:%s" % i


class Table:
    def __init__(self, name):
        self.columns = []
        self.name = name
        self.uniques = []
        self.constraints = []
        self.relations = []
        
    def addColumn(self, col):
        self.columns.append(col)

class Column:
    def __init__(self, name, datatype):
        self.name = name
        self.datatype = string.capitalize(string.lower(datatype))
        self.references = []
        self.uniqueCons = []
        
class Schema:
    def __init__(self):
        self.tables = {}
        self.sequences = []

    def __getitem__(self, a):
        return self.tables[a]

    def __setitem__(self, a, v):
        self.tables[a] = v
	
def makeSchema():
    user= raw_input('    User:')
    password=raw_input('Password:')
    database=raw_input('Database:')
    host=    raw_input('Hostname:')
    
    conn = sapdbapi.Connection(user,password,database,host)
    sch = Schema()

    objs = getObjects(conn, user)
    for obj in objs:
        if obj[1] == 'TABLE':
            t = Table(obj[0])
            d = descTable(conn, user, t.name)
            for i in d:
                t.addColumn(Column(i[0], i[1]))
            sch[t.name] = t
        elif obj[1] == 'SEQUENCE':
            sch.sequences.append(obj[0])
        
    return sch, conn, user

def makeTableGuess(tn):
    t = []
    bits = string.split(tn, '_')
    obits = map(string.capitalize, map(string.lower, bits))
    return string.join(obits, '')

def uniqueMe(fk, constraints, schema):
    #determine if my side of fk constraint is unique

    #get columns on this side
    col = fk.column
    
    #get unique constraints for this table
    unique = filter(lambda x:x.kind=='P',schema[fk.table].constraints)
    if col in unique:
            return 1
        
    return 0

def figureRelations(foreignkeys, constraints, schema):
    for fk in foreignkeys:
        if uniqueMe(fk, constraints, schema):
            cls1 = OneToOne
            cls2 = OneToOne
        else:
            cls1 = ManyToOne
            cls2 = OneToMany
        schema[fk.table].relations.append(cls1([fk.column], fk.reftable, [fk.refcolumn]))
        schema[fk.reftable].relations.append(cls2([fk.refcolumn], fk.table, [fk.column]))

def singular(text):
    if len(text) > 2 and text[-2:] == 'us':
        return text
    if text[-1] == 's':
        return text[:-1]
    else:
        return text

def multiple(text):
    if len(text) > 2 and text[-2:] == 'us':
        return text + 'es'
    if text[-1] == 's':
        return text
    elif text[-1] == 'y':
        return text[:-1] + 'ies'
    else:
        return text+'s'

def readSequences(tn, schema):
    ret = []
    seqs = schema.sequences
    fseqs = filter(lambda x, tn=tn: string.find(x, tn)!=-1, seqs)
    ans = 'Y'
    timeAround = 0
    while 1:
        timeAround = timeAround + 1
        if len(fseqs) == 1 and timeAround == 1:
            ans = ''
            while string.upper(ans) not in ('Y', 'N'):
                ans = raw_input('sequence %s? (y/n)' % fseqs[0])
                ans = string.upper(ans)
            if ans == 'Y':
                ans = raw_input('attr name:')
            ret.append((ans, fseqs[0]))

        if len(fseqs) != 1 or ans == 'N':
            if len(fseqs) != 0:
                for fi in range(len(fseqs)):
                    print '[%s] %s' % (fi+1, fseqs[fi])
                ans = raw_input('sequence # or N if not one of these:')
            else:
                ans = "n"
            try:
                ans = int(ans)
            except ValueError:
                for i in range(len(seqs)):
                    print '[%s] %s' % (i+1, seqs[i])
                ans = raw_input('sequence # (-1 to bail on table):')
                if int(ans) == -1:
                    break
                seqn = seqs[int(ans)-1]
            else:
                seqn = fseqs[ans-1]
            ans = raw_input('attr name:')
            ret.append((ans, seqn))
        while string.upper(ans) not in ('Y', 'N'):
            ans = string.upper(raw_input('done for table %s? (y/n)' % tn))
        if ans == 'Y':
            break
    return ret
                
def qcommafy(l):
    return string.join(map(lambda x: "'%s'" % x, l), ', ')

def genClasses(schema, uname, conn):
    ca = raw_input('connection alias:')
    
    out = cStringIO.StringIO()
    out.write(
"""# automatically generated by sapdbgenscript.py

import PyDO
    
# remove the next two lines if this will run under AED with
# the sql personality enabled (e.g. superteam)
# -or-
# edit the user/pw@inst string as appropriate

# import SQL
# SQL.initUser('xxx', 'user/pw@inst')

# If running this under AED with sql personality enabled, change xxx
# the the appropriate connection name

PyDO.DBIInitAlias(%s, 'pydo:sapdb:xxx')

""" % repr(ca))
    tableNameToClassName = {}
    for tn, t in schema.tables.items():
        cn = ''
        while not string.strip(cn): 
            guess = makeTableGuess(tn)
            cn = raw_input('name for class for table %s (default: %s):' % (
                tn, guess))
            if not cn:
                cn = guess


        tableNameToClassName[tn] = cn

    for tn, t in schema.tables.items():
        print 'table:', tn
        cn = tableNameToClassName[tn]
        out.write('\nclass %s(PyDO.PyDO):\n' % cn)
        out.write("    connectionAlias = '%s'\n" % ca)
        out.write("    table = '%s.%s'\n" % (uname, tn))
        out.write('    fields = (\n')
        for col in t.columns:
            out.write("        ('%s', '%s'),\n" % (col.name, col.datatype))
        out.write('    )\n')

        #write out unique list 
        wu = None
        wc = []
        for c in t.constraints:
            if c.kind == 'U' or c.kind == 'P':
                if not wu:
                    wu = 1
                    out.write('    unique = [')
                if len(c.columns) > 1:
                    wc.append("(%s)" %
                              string.join(map(lambda x:"'%s'" % x.column,
                                              c.columns), ', '))
                else:
                    wc.append("'%s'" % c.columns[0].column)

        # Add unique columns missed by constraint table.
        cur = conn.cursor()
        cur.execute('select COLUMNNAME from domain.indexcolumns '
                    'where owner=:p1 and tablename=:p2 and type=:p3',
                    (uname, tn, 'UNIQUE'))
        uniques = cur.fetchall()
        for unique in uniques:
            if not wu:
                wu = 1
                out.write('    unique = [')
            wc.append("'%s'" % unique[0])

        if wu:
            out.write(string.join(wc, ', '))
            out.write(']\n')
        del cur
        
        #write out sequences
        ans = ''
        while not ans:
            ans = raw_input('any sequences(y/n):')
            if string.upper(ans) in ('Y', 'N'):
                ans = string.upper(ans)
                break

        if ans == 'Y':
            seqs = readSequences(tn, schema)
            if seqs:
                out.write('    sequenced = {\n')
                for a, v in seqs:
                    out.write("        '%s': '%s',\n" % (a, v))
                    #schema.sequences[v-1]))
                out.write("    }\n")


        #write out auto-increment (serial) columns
        cur = conn.cursor()
        cur.execute('SELECT COLUMN_NAME, DATA_DEFAULT FROM SYS.ALL_TAB_COLUMNS '
                    'WHERE OWNER=:p1 AND TABLE_NAME=:p2',
                    (uname, tn))
        columns = cur.fetchall()
        serial_columns = {}
        for col in columns:
            if (col[1] is not None) and (col[1].upper().count('SERIAL') != 0):
                serial_columns[col[0]] = None
        del cur

        if len(serial_columns) != 0:
            out.write('    auto_increment = ' + str(serial_columns) + '\n')

        #write out foreign key methods
        for r in t.relations:
            oside = tableNameToClassName[r.theirTable]
            if isinstance(r, OneToOne) or isinstance(r, ManyToOne):
                out.write('    def get%s(self):\n' % singular(oside))
                out.write('        return %s.getUnique(' % oside)
                args = []
                for m, t in map(None, r.theirAttrs, r.myAttrs):
                    args.append("%s = self['%s']" % (m, t))
                out.write('%s)\n\n' % string.join(args, ', '))
            elif isinstance(r, OneToMany):
                out.write('    def get%s(self):\n' % multiple(oside))
                out.write('        return %s.getSome(' % oside)
                args = []
                for m, t in map(None, r.theirAttrs, r.myAttrs):
                    args.append("%s = self['%s']" % (m, t))
                out.write('%s)\n\n' % string.join(args, ', '))

            else: #ManyToMany
                if not r.methName:
                    out.write('    def get%sVia%s(self):\n' % (
                        multiple(oside),
                        tableNameToClassName[r.joinTable.name]))
                else:
                    out.write('    def %s(self):\n' % r.methName)
                out.write('        return self.joinTable(')
                out.write('%s, "%s", %s, %s, %s, %s)\n' % (
                    qcommafy(r.myAttrs), r.joinTable.name,
                    qcommafy(r.mySideJoinAttrs),
                    qcommafy(r.theirSideJoinAttrs),
                    oside, qcommafy(r.theirAttrs)))

    return out

def commafy(l):
    return string.join(l, ', ')

def makeM2MJoin(t, rels, schema):
    tn = t.name
    s1o = map(lambda x, t=rels[0].theirTable: '%s.%s' % (t, x),
              rels[0].theirAttrs)
    s1m = map(lambda x, t=tn: '%s.%s' % (t, x),
              rels[0].myAttrs)

    s2o = map(lambda x, t=rels[1].theirTable: '%s.%s' % (t, x),
              rels[1].theirAttrs)
    s2m = map(lambda x, t=tn: '%s.%s' % (t, x),
              rels[1].myAttrs)
    print 'From %s to %s' % (rels[0].theirTable, rels[1].theirTable)
    print '    via %s to %s\n        %s to %s' % (
        commafy(s1o), commafy(s1m), commafy(s2m), commafy(s2o))
    ans = ''
    print
    while ans not in ('Y', 'N'):
        ans = string.upper(raw_input('make method(y/n):'))
    if ans == 'Y':
        t1 = schema.tables[rels[0].theirTable].name
        t2 = schema.tables[rels[1].theirTable].name
        jt = t
        t1Meth = raw_input('Method Name for %s side(blank for no method):'% t1)
        t2Meth = raw_input('Method Name for %s side(blank for no method):'% t2)
        if t1Meth:
            schema[t1].relations.append(
                ManyToMany(rels[0].theirAttrs, jt, rels[0].myAttrs,
                           rels[1].myAttrs, rels[1].theirTable,
                           rels[1].theirAttrs, t1Meth)
                )
        if t2Meth:
            schema[t2].relations.append(
                ManyToMany(rels[1].theirAttrs, jt, rels[1].myAttrs,
                           rels[0].myAttrs, rels[0].theirTable,
                           rels[0].theirAttrs, t2Meth)
                )
        #check unique constraints and pk's

def doMany2Many(schema):
    for tn, t in schema.tables.items():
        m21ct = 0
        otables = []
        rels = []
        for r in t.relations:
            if isinstance(r, ManyToOne):
                m21ct = m21ct + 1
                otables.append(r.theirTable)
                rels.append(r)
                
        if m21ct > 1:
            print 'possible linkage table %s, for joining tables %s' % (
                tn, string.join(otables, ', '))
            #make the join for 2 tables
            if m21ct == 2:
                makeM2MJoin(t, rels, schema)
            else:
                for i in range(len(rels)):
                    for j in range(i+1, len(rels)):
                        makeM2MJoin(t, [rels[i], rels[j]], schema)
                    #print 'do not know how to join'
            print
                
def go():
    sch, conn, user = makeSchema()
    global constraints
    constraints = getConstraints(conn, user)
    foreignkeys = getForeignKeyColumns(conn, user)
    colConstraints = getColumnConstraints(conn, user)
    
    for colc in colConstraints:
        if constraints.has_key(colc.name):
           constraints[colc.name].columns.append(colc)

    for constraint in constraints.values():
        if constraint.table:
	    sch[constraint.table].constraints.append(constraint)

    figureRelations(foreignkeys,constraints, sch)
    doMany2Many(sch)
    o = genClasses(sch, string.upper(user), conn)
    filename = raw_input("file name to dump to:")
    open(filename, 'w').write(o.getvalue())

if __name__ == '__main__':
    go()
