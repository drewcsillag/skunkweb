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
import types
import htmlPython
import htmlSTML
import htmlCommon

def writeIndicies(nav, modules, stmlDocuments, destPath, filename):
    nnav = nav.newPlusAlter(up = filename, upText = 'STML/Code Index')
    out = htmlCommon.writer(open('%s/%s' % (destPath, filename), 'w'))
    out('<HTML><HEAD><TITLE>STML/Code Index</TITLE></HEAD>')
    out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
    out(nav.render(1))
    out('<H2>STML/Code Index</H2>')
    
    documents = htmlSTML.docFilter(stmlDocuments, 'Document')
    components = htmlSTML.docFilter(stmlDocuments, 'Component')
    datacomps = htmlSTML.docFilter(stmlDocuments, 'Data Component')

    if len(documents) > htmlSTML.MAX_DOCS_BEFORE_SEPARATE:
        out('<B><A HREF="document_index.html">Documents</A></B><P>')
        _writeSTMLIndex(nnav, documents, 'Documents',
                        destPath+'/document_index.html')
    else:
        out('<B>Documents</B><P>')
        _writeSTMLIndex(nnav, documents, 'Documents', out)

        
    if len(components) > htmlSTML.MAX_DOCS_BEFORE_SEPARATE:
        out('<B><A HREF="component_index.html">Components</A></B><P>')
        _writeSTMLIndex(nnav, components, 'Components',
                        destPath+'/component_index.html')
    else:
        out('<B>Components</B><P>')
        _writeSTMLIndex(nnav, components, 'Components', out)


    if len(datacomps) > htmlSTML.MAX_DOCS_BEFORE_SEPARATE:
        out('<B><A HREF="datacomp_index.html">Data Components</A></B><P>')
        _writeSTMLIndex(nnav, datacomps, 'Data Components',
                        destPath+'/datacomp_index.html')
    else:
        out('<B>Data Components</B><P>')
        _writeSTMLIndex(nnav, datacomps, 'Data Components', out)


    if len(modules) > htmlPython.MAX_TOC_ENTRIES_BEFORE_SEPARATE:
        out('<B><A HREF="module_index.html">Modules</A></B><P>')
        _writeModuleIndex(nnav, modules, destPath+'/module_index.html')
    else:
        out('<B>Modules</B><P>')
        _writeModuleIndex(nnav, modules, out)

    out('<BR><HR>')
    out(nav.render(0))
    out('</BODY></HTML>')

def _writeSTMLIndex(nav, things, legend, output):
    owndoc = 0
    if type(output) == types.StringType: #a filename, need to do own page
        owndoc = 1
        out = htmlCommon.writer(open(output, 'w'))
        out('<HTML><HEAD><TITLE>%s Index</TITLE></HEAD>' % legend)
        out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
        out(nav.render(1))
        out('<H2>%s Index</H2>' % legend)
    else:
        out = output
    things.sort(lambda x, y: cmp(x.name, y.name))
    lent = int(len(things) / 2)
    if len(things) % 2:
        lent = lent + 1
    col1 = things[:lent]
    col2 = things[lent:]


    out('<TABLE>')
    for c1, c2 in map(None, col1, col2):
        out('<TR>')
        if c1:
            out('<TD><A HREF="t%s.html">%s</A></TD>' % (
                htmlSTML._fixFileName(string.replace(c1.name, '/', '.')),
                c1.name))
        else:
            out('<TD> </TD>')

        if c2:
            out('<TD><A HREF="t%s.html">%s</A></TD>' % (
                htmlSTML._fixFileName(string.replace(c2.name, '/', '.')),
                c2.name))
        else:
            out('<TD> </TD>')

        out('</TR>')
    out('</TABLE>')

    if owndoc:
        out('<BR><HR>')
        out(nav.render(0))
        out('</BODY></HTML>')
        
def _writeModuleIndex(nav, modules, output):
    owndoc = 0
    if type(output) == types.StringType: #a filename, need to do own page
        owndoc = 1
        out = htmlCommon.writer(open(output, 'w'))
        out('<HTML><HEAD><TITLE>Module Index</TITLE></HEAD>')
        out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
        out(nav.render(1))
        out('<H2>Module Index</H2>')
    else:
        out = output
        
    modules.sort(lambda x, y: cmp(x.name, y.name))
    lent = len(modules) / 2
    if len(modules) % 2:
        lent = lent + 1
    col1 = modules[:lent]
    col2 = modules[lent:]

    out('<TABLE>')
    for c1, c2 in map(None, col1, col2):
        out('<TR>')
        if c1:
            out('<TD><A HREF="m.%s.html">%s</A></TD>' % (c1.name, c1.name))
        else:
            out('<TD> </TD>')

        if c2:
            out('<TD><A HREF="m.%s.html">%s</A></TD>' % (c2.name, c2.name))
        else:
            out('<TD> </TD>')

        out('</TR>')
    out('</TABLE>')

    if owndoc:
        out('<BR><HR>')
        out(nav.render(0))
        out('</BODY></HTML>')
