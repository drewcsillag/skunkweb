#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#index should be tuple of xref dict and ordered secNo list
from scanners import globals
import types
from htmlCommon import *
import string

def writeSkunkDoc(index, howto, destPath, nav):
    #write index.html (TOC) with link to CT index
    writeTOC(index, howto, destPath, nav)
    #recursively write sections (updating nav crap along way)
    for s in howto.sections:
        p, pt, n, nt = getNextPrev(s.secNo, index)
        nnav = nav.newPlusAlter(up = 'index.html',
                                upText = "Table Of Contents",
                                next = n, nextText = nt,
                                back = p, backText = pt)

        writeSection(index, nnav, destPath, s)

def writeTOC(index, howto, destPath, nav):
    out = writer(open(destPath + 'index.html', 'w'))
    out('<HTML><HEAD><TITLE>Table Of Contents</TITLE></HEAD>\n')
    out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
    out(nav.render(1))
    out('<HR>')
    if howto.title:
        out('<h2>%s</h2>' % render(howto.title))
    if howto.subtitle:
        out('<h3>%s</h3>' % render(howto.subtitle))

    if howto.author:
        out('<B>%s</B><P>' % render(howto.author))
        
    for sn in index['howto']['toc']:
        if sn != None:
            out('%s<A HREF="x.%s.html">%s: %s</A><BR>' % (
                string.count(sn, '.')*'&nbsp;&nbsp;&nbsp;&nbsp;', sn, sn,
                stripMarkup(index['howto']['secref'][sn].title)))
        else:
            out('<A HREF="code_and_templates_index.html">STML/Code Index</A>'
                '<BR>')
    
        
    out('<HR>')
    out(nav.render(0))
    out('</BODY></HTML>')

def stripMarkup(foo):
    s = []
    for i in foo.contents:
        if type(i) == types.StringType:
            s.append(i)
        else:
            s.append(stripMarkup(i))

    return string.join(s, '')

def render(x):
    return stripMarkup(x)

htmlMap = {
    'codeblock': ('pre', 1),
    'ul': 1,
    'ol': 1,
    'b': 1,
    'i': 1,
    'li': 1,
    'code': 1,
    'a': 1,
    'table': 1,
    'tr': 1,
    'td': 1,
    'th': 1,
    'p': 0,
    'br': 0,
    'pre': 1,
    'tt': 1,
    'dd': 1,
    'dt': 1,
    'dl': 1,
    'font': 1,
    'h1': 1,
    'h2': 1,
    'h3': 1,
    'nobr': 0,
    'wbr': 0,
    'hr': 0
}    
    
    
def renderBody(x, index):
    s = []
    for i in x.contents:
        if type(i) == types.StringType:
            s.append(i)
        elif i.tag == 'label':
            s.append('<A NAME="%s"></A>' % i.args['id'])
        elif i.tag == 'xref':
            refSec = i.args['id']
            try:
                sec = index['howto']['xref'][refSec]
            except KeyError:
                if globals.VERBOSE:
                    print 'invalid section reference %s' % refSec
                    #print 'keys=', index['howto']['xref'].keys()
                globals.ERRORS.append('invalid section reference %s' % refSec)
                s.append(renderBody(i, index))
            else:
                if type(sec) == type(()):
                    target = '#' + sec[1]
                    sec = sec[0]
                else:
                    target = ''
                s.append('<A HREF="x.%s.html%s">' % (sec.secNo, target))
                s.append(renderBody(i, index))
                if i.args.has_key('noparen'):
                    s.append(' %s: %s - %s</A>' % (
                        string.capitalize(sec.tag), sec.secNo,
                        stripMarkup(sec.title)))
                else:
                    s.append(' (%s: %s - %s)</A>' % (
                        string.capitalize(sec.tag), sec.secNo,
                        stripMarkup(sec.title)))
                
        else:
            if htmlMap.get(i.tag) is None:
                if globals.VERBOSE:
                    print 'skipping %s tag' % i.tag
                globals.ERRORS.append('skipping %s tag' % i.tag)
                continue
            tagmap = htmlMap[i.tag]
            if type(tagmap) == types.TupleType:
                outTag = tagmap[0]
                tagmap = tagmap[1]
            else:
                outTag = i.tag
            args = string.join(map(lambda x:'%s="%s"'%x, i.args.items()), ' ')
            if args:
                args = ' ' + args
            if not tagmap:
                args = args+'/'
            s.append('<%s%s>' % (outTag, args))
            s.append(renderBody(i, index))
            if tagmap == 1:
                s.append('</%s>' % outTag)
    return string.replace(string.join(s, ''), '\n\n', '\n<p>')


def getNextPrev(secNo, index):
    l = index['howto']['toc']
    a = l.index(secNo)
    if a == 0:
        prev = None
        prevText = None
    else:
        sec = index['howto']['secref'][l[a-1]]
        prev = 'x.%s.html' % sec.secNo
        prevText = stripMarkup(sec.title)
        
    if a == (len(l) - 1):
        next = None
        nextText = None
    else:
        if l[a+1] != None:
            sec = index['howto']['secref'][l[a+1]]
            next = 'x.%s.html' % sec.secNo
            nextText = stripMarkup(sec.title)
        else:
            next = 'code_and_templates_index.html'
            nextText = 'STML/Code Index'
            
    return prev, prevText, next, nextText
        
def writeSection(index, nav, destPath, section):
    out = writer(open(destPath + 'x.%s.html' % section.secNo, 'w'))
    out('<HTML><HEAD><TITLE>%s: %s -- %s</TITLE></HEAD>\n' % (
        string.capitalize(section.tag), section.secNo,
        stripMarkup(section.title)))
    out('<BODY BGCOLOR=WHITE FGCOLOR=BLACK>')
    out(nav.render(1))
    out('<HR>')
    out('<H2>%s: %s -- %s</H2>' % (
        string.capitalize(section.tag), section.secNo, render(section.title)))

    writeSectionTOC(out, section)

    out(renderBody(section, index))
        
    out('<HR>')
    out(nav.render(0))
    out('</BODY></HTML>')

    for s in section.sections:
        p, pt, n, nt = getNextPrev(s.secNo, index)
        nnav = nav.newPlusAlter(up = 'x.%s.html' % section.secNo,
                                upText = stripMarkup(section.title),
                                next = n, nextText = nt,
                                back = p, backText = pt)
                                
        writeSection(index, nnav, destPath, s)

def writeSectionTOC(out, section):
    for s in section.sections:
        out('<A HREF="x.%s.html">%s: %s - %s</A><BR>' % (
            s.secNo, string.capitalize(s.tag), s.secNo, render(s.title)))
    if section.sections:
        out('<P>')
