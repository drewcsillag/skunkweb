#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import globals
import os
from DT import DTTags, DTTagRegistry, DTLexer, DTParser, DTUtil
import DT
import common
import string
import types
        
tagConf = {
    #name, isempty
    'loop': 0,
    'for': 0,
    'val': 1,
    'call': 1,
    'continue': 1,
    'break': 1,
    'else': 1,
    'elif': 1,
    'if': 0,
    'while': 0,
    'comment': 0,
    '#': 0,
    'raise': 1,
    'except': 1,
    'finally': 1,
    'try': 0,
    'default': 1,
    'halt': 1,
    'spool': 0,

    #from templating persona
    'cache': 1,
    'component': 1,
    'datacomp': 1,
    'include': 1,
    'brandcomponent': 1,
    'branddatacomp': 1,
    'brandinclude': 1,
    'date': 1,
    'doc': 0,
    'import': 1,
    'msg': 1,
    'redirect': 1,
    'sendmail': 1,
    'http_get': 1,
    'return': 1,
    'set': 1,
    'log': 1,
    'warn':1,
    'error':1,
    'debug':1,
    'catalog':1,
    'multicatalog':1,
    'curl': 1,
    'url': 1,
    'img': 1,
    'form': 1,
    'retain': 1,
    'hidden': 1,
    'args': 1,
    'compargs': 1,

    #periscopio
    'ad': 1,
    'esp': 0,
    'por': 0,
    'eng': 0,

    #sql
    'sql': 1,
    }
    
class boinkTag(DTTags.DTTag):
    """tag class used for parsing STML"""
    def __init__(self, name, isEmpty):
        DTTags.DTTag.__init__(self, name, isEmpty)

    def parseBlock(self, text, taglist, start, tagreg, name):
        if self.tagname not in ('#', 'comment'):
            return DTTags.DTTag.parseBlock(self, text, taglist, start,
                                           tagreg, name)
        func = DTTags.GenericCommentTag.__dict__['parseBlock']
        return func(self, text, taglist, start, tagreg, name)
    
def _makeRegistry():
    tr = DTTagRegistry.DTTagRegistry()
    for k, v in tagConf.items():
        tr.addTag( boinkTag( k, v ) )
    return tr

def _parseSTMLDocument( filename, contents ):
    #tagRegistry is global
    try:
        tagList = DTLexer.doTag( contents, filename )
    except:
        return
    newtaglist = []
    #filter out unknown tags
    for i in tagList:
        if type(i) != type('') and tagRegistry.has_key(i.tagname):
            newtaglist.append(i)
        elif type(i) == type(''):
            newtaglist.append(i)
            
    return DTParser.parseit( contents, newtaglist, tagRegistry, filename )

def _findTags(tree, kind):
    if type(kind) == types.StringType:
        kind = (kind,)
    foundTags = []
    for i in tree.children:
        if isinstance( i, DT.DTLexer.DTToken ) and i.tagname in kind:
            foundTags.append(i)
        elif isinstance( i, DT.DTParser.Node ):
            foundTags.extend( _findTags( i, kind ) )
        else:
            pass
    return foundTags

def _findDocStrings(tree):
    docBlocks = []
    if not isinstance(tree, DT.DTParser.Node):
        return []

    if (isinstance(tree.children[0], DT.DTLexer.DTToken)
        and tree.children[0].tagname == 'doc'):
        docBlocks.append(tree)
    else:
        for i in tree.children:
            if isinstance(i, DT.DTParser.Node):
                docBlocks.extend(_findDocStrings(i))
    return docBlocks

_depSpecs = {
    'datacomp': ['var', 'name'],
    'include': ['name'],
    'component': ['name'],
    'branddatacomp': ['var', 'name'],
    'brandinclude': ['name'],
    'brandcomponent': ['name'],
    }

class STMLDocument:
    def __init__(self, name, source, kind):
        self.kind = kind
        self.name = name
        self.source = source
        self.parseDocument()
        self.imports = []
        self.caches = []
        self.dependancies = []

        self.usedBy = [] #filled in by renderer (if applicable)
        if self.parsed is not None:
            self.getIncludes()
            self.getComponents()
            self.getDataComponents()
            self.getDependancies()
            self.getImports()
            self.getCaches()
            self.getDocString()
        else:
            if globals.VERBOSE:
                print 'document %s failed to parse' % name
            globals.ERRORS.append('document %s failed to parse' % name)
            self.includes = self.brandincludes = []
            self.components = self.brandcomponents = []
            self.datacomps = self.branddatacomps = []
            self.docString = 'THIS DOCUMENT FAILED TO PARSE!'
        
    def parseDocument(self):
        try:
            self.parsed = _parseSTMLDocument(self.name, self.source)
        except:
            self.parsed = None

    def _getDependsOnFull(self, tagname):
        tags = _findTags(self.parsed, tagname)
        if not tags:
            return []
        l = []
        for tag in tags:
            #print 'TAG=', tag.tagname
            args = DTUtil.tagCall(tag, _depSpecs[tag.tagname], kwcol='kw')
            l.append((tag.tagname, args['name'], args['kw']))
        return l

    def _getDependsOn(self, tagname):
        return map(lambda x:x[1], self._getDependsOnFull(tagname))
    
    def getDependancies(self):
        self.dependancies = map(
            lambda (tn,n,a):[tn, n, a.get('cache')],
            self._getDependsOnFull(('include', 'component', 'datacomp',
                                    'brandinclude', 'brandcomponent',
                                    'branddatacomp')))
        
    def getIncludes(self):
        self.includes = self._getDependsOn('include')
        self.brandincludes = self._getDependsOn('brandinclude')

    def getComponents(self):
        self.components = self._getDependsOn('component')
        self.brandcomponents = self._getDependsOn('brandcomponent')
        
    def getDataComponents(self):
        self.datacomps = self._getDependsOn('datacomp')
        self.branddatacomps = self._getDependsOn('branddatacomp')
        
    def getImports(self):
        tags = _findTags(self.parsed, 'import')
        for tag in tags:
            args = DTUtil.tagCall(tag, ['module', ('items', 'None')])
            self.imports.append(args['module'])

    def getCaches(self):
        tags = _findTags(self.parsed, 'cache')
        if not tags:
            return
        for tag in tags:
            args = DTUtil.tagCall( tag,
                                   [('until', 'None'), ('duration', 'None')])
            if args['until'] != None:
                self.caches.append(('until', args['until']))
            else:
                self.caches.append(('duration', args['duration']))

    def getDocString(self):
        tags = _findDocStrings(self.parsed)#Tags(self.parsed, 'doc')
        if not tags:
            self.docString = ''
            return
        try:
            tag = string.join( tags[0].children[1:-1], '' )
        except AttributeError:
            print tags[0], dir(tags[0])
            print tags, dir(tags)
            raise
        
        self.docString = common.doDocString(tag)

    def relativize(self, targetFile):
        if targetFile[0] == '/':
            return targetFile
        fromFile = self.name
        path, filename = os.path.split(fromFile)
        newPath = os.path.normpath(path+'/'+targetFile)
        newPath = string.replace(newPath, '//', '/')
        return newPath

    def linkify(self, targetFile):
        return string.replace(self.relativize(targetFile), '/', '.')
    
def processFile( filename, kind ):
    contents = open( filename, 'r' ).read()
    try:
        tree = _parseSTMLDocument( filename, contents )
    except:
        if globals.VERBOSE:
            print 'error while parsing', filename
        globals.ERRORS.append('error while parsing %s'% filename)
        raise
    if not tree:
        return
    doc = STMLDocument(filename, kind)
          
#create global tag registry
tagRegistry=_makeRegistry()


def getExtension(name):
    ind = string.rfind(name, '.')
    if ind:
        return name[ind:]
    return ''
    
def isSTML(file):
    return getExtension(file) in ('.html', '.comp', '.dcmp')

def getSTMLKind(file):
    ext = getExtension(file)
    return {'.html': 'Document',
            '.comp': 'Component',
            '.dcmp': 'Data Component'
            }[ext]
        
def doDir(dirName, exclude, rootRel=''):
    if dirName in exclude:
        return []
    if globals.VERBOSE:
        print 'processing dir', dirName
    stmls = []
    files = os.listdir(dirName)
    for file in files:
        fullFilename = '%s/%s' % (dirName, file)
        if os.path.isfile(fullFilename) and isSTML(file):
            kind = getSTMLKind(file)
            if globals.VERBOSE:
                print 'processing file', fullFilename
            contents = open(fullFilename).read()
            stmls.append(STMLDocument('%s/%s' % (rootRel, file), contents,
                                      kind))
        elif os.path.isdir(fullFilename):
            stmls.extend(doDir(fullFilename, exclude, '%s/%s' % (rootRel,
                                                                 file)))
    return stmls

if __name__ == '__main__':
    x = doDir('/home/drew/devel/support.skunk.org/rundata')
