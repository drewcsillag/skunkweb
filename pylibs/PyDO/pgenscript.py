#!/usr/local/bin/python
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
import cStringIO
import string
import pgdb


def readSequences(tn, schema):
    ret = []
    seqs = map(lambda x: x[0], schema.sequences)
    #print "sequences is", seqs
    fseqs = filter(lambda x, tn=tn: x.find(tn)!=-1, seqs)
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

class Schema:
    def __init__(self):
        self.tables = {}
        self.sequences = []

    def __setitem__(self, a, v):
        self.tables[a] = v

    def __getitem__(self, a):
        return self.tables[a]

    
class Table:
    def __init__(self, name, columns, uniques):
        self.name = name
        self.columns = columns
        self.uniques = uniques
        self.references = []
        self.relations = []
        
class Column:
    def __init__(self, name, datatype, colno):
        self.datatype = datatype
        self.name = name
        self.colno = colno
        
class References:
    def __init__(self, fromTable, toTable,
                 fromColumns, toColumns):
        self.fromTable = fromTable
        self.toTable = toTable
        self.fromColumns = fromColumns
        self.toColumns = toColumns
        
def getObjects(conn):
    #get TABLEs, SEQUENCEs and INDEXes
    cur = conn.cursor()
    cur.execute("SELECT RELNAME, RELKIND FROM PG_CLASS WHERE"
                " substr(RELNAME, 1, 3) != 'pg_' AND"
                " RELKIND IN ('S', 'r')")
    return cur.fetchall()

def descTable(conn, table):
    #get columns and datatypes for a table
    cur = conn.cursor()
    cur.execute('SELECT A.ATTNAME, T.TYPNAME, A.ATTNUM'
                ' FROM PG_ATTRIBUTE A, PG_TYPE T,'
                ' PG_CLASS C WHERE A.ATTTYPID = T.OID AND A.ATTNUM > 0 AND'
                " A.ATTRELID = C.OID AND C.RELNAME='%s'" % table)
    return cur.fetchall()

def getUniqueAndPKConstraints(conn):
    cur = conn.cursor()
    cur.execute('select c1.relname, c2.relname, i.indkey, i.indisunique,'
                ' i.indisprimary'
                ' from pg_class c1, pg_class c2, pg_index i'
                ' where i.indexrelid = c1.oid and i.indrelid = c2.oid'
                " and (i.indisunique = 't' or i.indisprimary = 't')"
                " and substr(c2.relname, 1, 3)!='pg_'")

    d = {}
    for indn, tn, ic, iu, ip in cur.fetchall():
        ol = d.get(tn, [])
        ol.append(ic)
        d[tn] = ol
    return d
        

def getRIConstraints(conn):
    cur = conn.cursor()
    cur.execute('''
    select c1.relname, c2.relname, t.tgnargs, t.tgargs
    from pg_class c1, pg_class c2, pg_trigger t
    where t.tgrelid = c1.oid and
          t.tgconstrrelid = c2.oid and
          t.tgisconstraint = 't' and tgfoid = 1644
    ''')
    r = []
    for i in cur.fetchall():
        rn1, rn2, nargs, args = i
        r.append((rn1, rn2, nargs, args.split(r'\000')[:-1]))
    return r



def main():
    sch = Schema()
    connstr = raw_input("connect string>")
    conn = pgdb.connect(connstr)
    tabseq = getObjects(conn)
    sch.sequences = filter(lambda x: x[1] == 'S', tabseq)
    tables = filter(lambda x: x[1] == 'r', tabseq)

    unpk = getUniqueAndPKConstraints(conn)

    #create tables
    for i, crapola in tables:
        td = descTable(conn, i)
        cols = {}
        uniques = []
        for na,t,nu in td:
            cols[na] = Column(na, t, nu)
            #print 'table', i
        for colnostr in unpk.get(i, []):
            colnos = map(int, colnostr.split())
            #print 'column nos', colnos, map(lambda x:x.name, cols.values())
            colnames = [
                filter(lambda x, n=colnos: x.colno in n,
                       cols.values())
                ]
            colnames = map(lambda x: x.name, colnames[0])
            #print colnames
            #print 
            if colnames: 
                    uniques.append(colnames)
        sch.tables[i] = Table(i, cols, uniques)

    for ft, tt, na, a in getRIConstraints(conn):
        ftf = 1
        cols = a[4:]
        fromcols = []
        tocols = []
        for i in cols:
            if ftf:
                fromcols.append(i)
            else:
                tocols.append(i)
            ftf = not ftf
        sch.tables[ft].references.append(
            References(ft, tt, fromcols, tocols))
        
    return sch, connstr

##################################################
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

def makeTableGuess(tn):
    t = []
    bits = string.split(tn, '_')
    obits = map(string.capitalize, map(string.lower, bits))
    return string.join(obits, '')

def commafy(l):
    return string.join(l, ', ')

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

def isUnique(table, cols):
    for i in table.uniques:
        if len(i) != len(cols):
            continue
        for j in cols:
            if not j in i:
                break
        else:
            return 1
    return 0

def figureRelations(schema):
    for tn, v in sch.tables.items():
        #doprint = 0
        #if tn == 'm12m2':
        #    print
        #    doprint = 1
        if not v.references:
            continue
        for r in v.references:
            tt = r.toTable
            fc = r.fromColumns
            tc = r.toColumns

            fu = isUnique(v, fc)
            tu = isUnique(sch.tables[tt], tc)

            #if doprint:
            #    print 'm12m2', fc, fu, v.uniques
            #    print tt, tc, tu
            #    print 
                
            if fu and tu:
                cf = ct = OneToOne
            elif fu:
                cf = OneToMany
                ct = ManyToOne
            else:
                ct = OneToMany
                cf = ManyToOne

            v.relations.append(cf(fc, tt, tc))
            sch.tables[tt].relations.append(ct(tc, tn, fc))

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

def genClasses(schema, connstr):
    ca = raw_input('connection alias:')
    
    out = cStringIO.StringIO()
    out.write(
"""# automatically generated by pgenscript.py

import PyDO
    
PyDO.DBIInitAlias(%s, 'pydo:postgresql:%s')

""" % (repr(ca), connstr))
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
        out.write('class %s(PyDO.PyDO):\n' % cn)
        out.write("    connectionAlias = '%s'\n" % ca)
        out.write("    table = '%s'\n" % (tn))
        out.write('    fields = (\n')
        #print 't.columns is', t.columns.values()
        for col in t.columns.values():
            out.write("        ('%s', '%s'),\n" % (col.name, col.datatype))
        out.write('    )\n')

        #write out unique list 
        wu = None
        wc = []

        if t.uniques:
            out.write('    unique = %s\n\n' % (map(tuple, t.uniques)))

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

def qcommafy(l):
    return string.join(map(lambda x: "'%s'" % x, l), ', ')


sch, cs = main()
figureRelations(sch)
doMany2Many(sch)
o = genClasses(sch, cs)
filename = raw_input("file name to dump to:")
open(filename, 'w').write(o.getvalue())
