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
import types
from DT import DTLexer
from scanners import globals, STMLScanner
import os
import string
import scanners.common
import htmlCommon
from docStringHTMLRenderer import renderDocString
from scanners.common import plainEscape

MAX_DOCS_BEFORE_SEPARATE = 30
STML_COLORS = {
    'Document': '#ffdddd',
    'Component': '#ddffdd',
    'Data Component': '#ddddff'
    }

def docFilter(docs, kind):
    return filter(lambda x, k=kind: x.kind == k, docs)

def _fixFileName(name):
    last = ''
    while last != name:
        last = name
        name = string.replace(name, '..', '.')
        name = string.replace(name, '//', '/')
    return name
    
def writeSTMLDocuments(index, stmlDocuments, destPath, nav):
    documents = docFilter(stmlDocuments, 'Document')
    components = docFilter(stmlDocuments, 'Component')
    datacomps = docFilter(stmlDocuments, 'Data Component')

    _computeDependencies(index['stml'])
    if 0:
        import code
        code.interact(banner = "dependancy tool", local=locals())
        
            
    onav = nav
    if len(documents) > MAX_DOCS_BEFORE_SEPARATE:
        nav = nav.newPlusAlter(up = 'document_index.html',
                               upText='Document Index')
    _writeSTMLDocs(index, documents, destPath, nav)
    nav = onav
    if len(components) > MAX_DOCS_BEFORE_SEPARATE:
        nav = nav.newPlusAlter(up = 'component_index.html',
                               upText='Component Index')
    _writeSTMLDocs(index, components, destPath, nav)
    nav = onav
    if len(datacomps) > MAX_DOCS_BEFORE_SEPARATE:
        nav = nav.newPlusAlter(up = 'datacomp_index.html',
                               upText='Data Component Index')
    _writeSTMLDocs(index, datacomps, destPath, nav)

def _writeSTMLDocs(index, docs, destPath, nav):
    for doc in docs:
        _writeSTML(index, doc, destPath, nav)
        
def _writeSTML(index, doc, destPath, nav):
    out = htmlCommon.writer(open(_fixFileName(destPath + '/t.%s.html' % (
        _fixFileName(string.replace(doc.name,'/','.')))), 'w'))
    out('<HTML><HEAD><TITLE>%s %s</TITLE></HEAD>\n' % (doc.kind, doc.name))
    out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
    out(nav.render(1))
    out('<HR><TABLE CELLSPACING=0 BORDER=0 width=100%><TR>')
    out('<TD COLSPAN=2 BGCOLOR=%s>' % STML_COLORS[doc.kind])
    out('<H2>%s <code>%s</code></H2>' % (doc.kind, doc.name))
    out('<font size=-1>%s</font>' % renderDocString(doc.docString))

    color = STML_COLORS[doc.kind]
    _writeDeps(out, color, 'Includes', index, doc, doc.includes)
    _writeBrandedDeps(out, color, 'Branded Includes', index, doc,
                      doc.brandincludes)
    _writeDeps(out, color, 'Components', index, doc, doc.components)
    _writeBrandedDeps(out, color, 'Branded Components', index, doc,
                      doc.brandcomponents)
    _writeDeps(out, color, 'Data Components', index, doc, doc.datacomps)
    _writeBrandedDeps(out, color, 'Branded Data Components', index, doc,
                      doc.branddatacomps)

    _writeCaches(out, color, doc)
    _writeImports(out, color, index, doc)
    out('</TABLE>')
    _writeSource(out, doc)
    _writeDepTree(out, doc, index)
    out('<HR>')
    _writeUsedBy(out, color, doc, index)
    out(nav.render(0))
    out('</BODY></HTML>')

def _writeUsedBy(out, color, doc, index):
    if doc.usedBy:
        out('<TABLE>')
        _writeDeps(out, color, 'Used By', index, doc, doc.usedBy)
        out('</TABLE>')

def _uniqify( list ):
    d = {}
    for i in list:
        d[i] = 1
    l = d.keys()
    l.sort()
    return l

def _writeDeps(out, color, legend, index, doc, depnames):
    depl = []
    depnames = _uniqify(depnames)
    for depname in depnames:
        fdn = doc.relativize(depname)

        if index['stml'].has_key(fdn):
            link = _fixFileName(doc.linkify(depname))
            depl.append('<A HREF="t%s.html"><CODE>%s</CODE></A>' % (
                link, depname))
        else:
            depl.append('<CODE>%s</CODE>' % depname)
        
    deps = string.join(depl, ', ')

    if depnames:
        out(('<TR><TD BGCOLOR=%s VALIGN=TOP><B>%s:</B></TD><TD'
             ' border=1>%s</TD></TR>') % (color, legend, deps))

def _findBrandMatches(fdn, index):
    extind = string.rindex(fdn, '.')
    ext = fdn[extind:]
    lenext = -len(ext)
    extind = extind + 1
    root = fdn[:extind]
    retlist = []
    for l in index['stml'].keys():
        #if root and extension match
        if l[:extind] == root and l[lenext:] == ext:
            retlist.append(l)
    print 'branded matches are:',retlist
    return retlist

def _writeBrandedDeps(out, color, legend, index, doc, depnames):
    depl = []
    depnames = _uniqify(depnames)
    for depname in depnames:
        fdn = doc.relativize(depname)
        bms = _findBrandMatches(fdn, index)

        if index['stml'].has_key(fdn):
            link = _fixFileName(doc.linkify(depname))
            depl.append('<A HREF="t%s.html"><CODE>%s</CODE></A><BR>' % (
                link, depname))
        else:
            depl.append('<CODE>%s</CODE><BR>' % depname)
            
        for bm in bms:
            if bm == fdn: continue
            link = _fixFileName(doc.linkify(bm))
            depl.append(('&nbsp;&nbsp;&nbsp;&nbsp;<A HREF="t%s.html">'
                        '<CODE>%s</CODE></A><BR>') % (link, bm))
        
    deps = string.join(depl, '\n')

    if depnames:
        out(('<TR><TD BGCOLOR=%s VALIGN=TOP><B>%s:</B></TD><TD'
             ' border=1>%s</TD></TR>') % (color, legend, deps))

def _writeCaches(out, color, doc):
    caches = _uniqify(doc.caches)
    cachel = []
    for cache in caches:
        cachel.append('%s %s' % cache)
    cacheStr = string.join(cachel, ', ')
    if caches:
        out(('<TR><TD BGCOLOR=%s VALIGN=TOP><B>Cache Lifetimes:</B></TD>'
            '<TD border=1>%s</TD></TR>') % (
                color, scanners.common.plainEscape(cacheStr)))

def _writeImports(out, color, index, doc):
    imps = _uniqify(doc.imports)
    impl = []
    for imp in imps:
        if index['code'].has_key(imp):
            impl.append('<A HREF="m.%s.html"><CODE>%s</CODE></A>' % (
                imp, imp))
        else:
            impl.append('<CODE>%s</CODE>' % imp)
    if imps:
        out(('<TR><TD BGCOLOR=%s VALIGN=TOP><B>Imports: </B></TD>'
            '<TD>%s</TD></TR>') % (color, string.join(impl, ', ')))

def _writeSource(out, doc):
    if doc.source:
        out('<HR><H2>Source Code</H2>')
        out('<PRE><CODE>%s</CODE></PRE>' %
            _colorizeSource(doc.source))

            
def _computeDependencies(index):
    if globals.VERBOSE:
        print 'computing stml dependancies'
    for docname, doc in index.items():
        for attr in ('includes', 'components', 'datacomps', 'brandincludes',
                     'brandcomponents', 'branddatacomps'):
            val = getattr(doc, attr)
            for using in val:
                using = [_fixFileName(doc.relativize(using)),]
                if attr[:5] == 'brand':
                    using = _findBrandMatches(using[0], {'stml': index})
                for u in using:
                    try:
                        index[u].usedBy.append(docname)
                    except KeyError, v:
                        if globals.VERBOSE:
                            print ("depended document %s in %s doesn't exist!"
                                   % (v, docname))
                        globals.ERRORS.append(("depended document %s in %s"
                                               " doesn't exist!") % (
                                                   v, docname))

def _writeDepTree(out, doc, index):
    import cStringIO
    oout = out
    oo = cStringIO.StringIO()
    out = htmlCommon.writer(oo)
    out('<HR>')
    out('<H2>Component Dependancy Tree</H2>')
    out('<UL>')
    md = _writeDependancyTree(out, doc, index,
                         STMLScanner.getSTMLKind(doc.name),
                         hasRequest = (
                             doc.kind == 'Document' and 1 or 0))
    out('</UL>')

    if md > 0:
        oout(oo.getvalue())
    
def _writeDependancyTree(out, doc, index, usedAs, cacheable=0, called_cache=0,
                         depth=0,
                         parentDocName="/index.html",
                         hasRequest=1, recurList = []):
    maxDepth = depth
    indent = ('&nbsp;' * 4)
    fullName = doc.name
    #print 'fullName=', fullName
    if fullName in recurList:
        out('<LI><font color=red>%s -- component loop detected</font></li>'
            % fullName)
        return
    recurList = recurList + [fullName]
    #write self
    if doc.kind == 'Document':
        out(("<LI><i><B>Document</B></i> %s "
             "<FONT SIZE=-2>(has REQUEST and RESPONSE objects)</FONT></LI>")
            % fullName)
    else:
        marker = doc.kind[0]
        if hasRequest:
            hrstr = " (has REQUEST and RESPONSE objects)"
        else:
            hrstr = ""

        if cacheable and called_cache:
            cacheStr = " (cached )<BR>" + _formatCaches(cacheable)
        elif cacheable:
            cacheStr = " (<font color=red>&lt;:cache:&gt; tag but not called cached</font> )<BR>" + _formatCaches(cacheable)
        elif called_cache:
            cacheStr = (" (<font color=red>cached but no"
                        " &lt;:cache:&gt; tag</font> )")
        else:
            cacheStr = ""

        psStr = hrstr + cacheStr 
            
        if psStr:
            psStr = ' <FONT SIZE=-2>%s</FONT>' % psStr[1:]
        out('<LI><i>%s</i> <A HREF="t%s.html"><B>%s</B></A>%s</LI>' % (
            usedAs, 
            string.replace(fullName, '/', '.'), fullName,
            psStr
            ))

    out('<UL>')
    #write children
    for dtype, d, cc in doc.dependancies:
        try:
            nd = index['stml'][doc.relativize(d)]
        except:
            out("<LI><i>%s</i><B>%s</B>%s</LI>" % (
                {'datacomp': 'Data Component',
                 'component': 'Component',
                 'include': 'Include',
                 'branddatacomp':  'Branded Data Component',
                 'brandcomponent': 'Branded Component',
                 'brandinclude':   'Branded Include',
                 }[dtype],
                d, (called_cache and ", called cached" or "")))
        else:
            link = _fixFileName(doc.linkify(d))
            rdepth = _writeDependancyTree(
                out, nd, index,
                {'datacomp': 'Data Component',
                 'component': 'Component',
                 'include': 'Include',
                 'branddatacomp':  'Branded Data Component',
                 'brandcomponent': 'Branded Component',
                 'brandinclude':   'Branded Include'
                 }[dtype],
                nd.caches,
                cc,
                depth+1, fullName,
                (dtype != 'include' and (0,) or (hasRequest,))[0],
                recurList)
            maxDepth = max(maxDepth, rdepth)
    out('</UL>')
    return maxDepth

def _colorizeSource(source):
    s = []
    tokens = DTLexer.doTag(source, 'foo')
    for tok in tokens:
        if type(tok) == types.StringType:
            s.append(scanners.common.plainEscape(tok))
        else:
            s.append(_colorizeTag(source, tok))
    return string.join(s, '')

def _colorizeTag(source, tag):
    s=[]
    tagtext = tag.tagText()
    #print 'args = ', tagtext, tag.name
    tagnameEnd = string.index(tagtext, tag.tagname) + len(tag.tagname)
    s.append('<FONT COLOR=BLUE>%s' % tagtext[:tagnameEnd])
    argsText = tagtext[tagnameEnd:len(tagtext)-2]
    if argsText:
        s.append('</FONT>%s<FONT COLOR=BLUE>' %
                 _colorizeTagArgs(tagtext[2:-2]))
        #scanners.common.plainEscape(argsText))

    s.append(':&gt;</FONT>')
    return string.join(s, '')

def _colorizeTagArgs(tagString):
    from DT.DTLexer import pcre,wsmatch,tagContentsRe
    #restolen from DT.DTLexer.processTag

    s = []
    tagname=''
    off=0
    
    tnmatch = None
    while not tnmatch:
        wsmatch = wsre.match(tagString, off, len(tagString), pcre.ANCHORED)
        if not wsmatch:
            tnmatch = plainre.match(tagString, off, len(tagString),
                                    pcre.ANCHORED)
            if not tnmatch:
                raise LexicalError('invalid tag name', tagString[off:off+10])
            else:
                break
        off = wsmatch[0][1]
                                
    tagname=tagString[tnmatch[0][0]:tnmatch[0][1]]

    off=tnmatch[0][1]
    lts=len(tagString)
    while off<lts:
        match=tagContentsRe.match(tagString, off, lts, pcre.ANCHORED)
        if match is None:
            raise LexicalError('invalid tag text name',
                               tagString[off:off+10])
        if match[WHITESPACE] != (-1, -1):
            mb, me=match[WHITESPACE]
            s.append(tagString[mb:me])
            off=me
        elif match[PLAIN] != (-1, -1):
            mb, me=match[PLAIN]
            s.append('<FONT COLOR=PURPLE>%s</FONT>' %
                     plainEscape(tagString[mb:me]))
            off=me
        elif match[PLAINEQ] != (-1, -1):
            mb, me=match[PLAINEQ]
            tmb, tme=match[PLAINEQVAL]

            vvv = tagString[mb:tme]
            if vvv[0]=="`":
                s.append('<FONT COLOR=GREEN>')
            else:
                s.append('<FONT COLOR=PURPLE>')
            s.append(plainEscape(vvv))
            s.append('</FONT>')
            off=tme
        elif match[PLAINEQQ] != (-1, -1):
            mb, me=match[PLAINEQQ]
            tmb, tme=match[PLAINEQQVAL]
            if tagString[tmb] == "`":
                s.append('<FONT COLOR=GREEN>')
            else:
                s.append('<FONT COLOR=PURPLE>')
            s.append(plainEscape(tagString[mb:tme]))
            s.append('</FONT>')
            off=tme
        elif match[QUOTONLY] != (-1, -1):
            mb, me=match[QUOTONLY]

            vvv = tagString[mb:me]
            if vvv[0] == "`":
                s.append('<FONT COLOR=GREEN>')
            else:
                s.append('<FONT COLOR=PURPLE>')
            s.append(plainEscape(vvv))
            s.append('</FONT>')

            off=me
        else:
            raise LexicalError('unknown text in tag', tagString[off:off+10])

    return string.join(s,'')

def _formatCaches(c):
    s = []
    s.append('<DL><DT><B>Cache Lifetimes</B></DT><DD>')

    for ck, cv in c:
        s.append('%s: %s<BR>' % (ck, cv))
        
    s.append('</DD></DL>')
    return string.join(s, '')
