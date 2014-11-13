from DT.DTUtil import tagCall
from DT.DTCompilerUtil import pyifyArgs, pyifyKWArgs, tagDebug, getTempName
from DT.DTTags import DTTag
from AE.Cache import tagRegistry
import computils
import slotutils
import SkunkWeb


class SlotTag(DTTag):
    """
    <:slot slotname **kwargs:>

    equivalent to getSlot(slotname)(**kwargs)
    """
    def __init__(self, defaultSlotMapName='SLOTS'):
        self.defaultSlotMapName=defaultSlotMapName
        DTTag.__init__(self,
                       'slot',
                       isempty=1)


    def genCode(self, indent, codeout, tagreg, tag):
        tagDebug(indent, codeout, tag)
        args=tagCall(tag,
                     (('name',),
                      ('slotmap', None)),
                     kwcol='kw')
        args=pyifyArgs(tag, args)
        kw=pyifyKWArgs(tag, args['kw'])
        mapvar=args['slotmap']
        if mapvar is None:
            mapvar=self.defaultSlotMapName
        slotvar=getTempName()
        codeout.write(indent,
                      '%s=%s.get(%s, '')' % (slotvar, mapvar, args['name']))
        codeout.write(indent, "if callable(%s):" % slotvar)
        codeout.write(indent+4,
                      '__h.OUTPUT.write(%s(**%s))' % (slotvar, kw))
        codeout.write(indent, "elif %s:" % slotvar)
        codeout.write(indent+4, "__h.OUTPUT.write(%s)" % slotvar)
        codeout.write(indent, "del %s" % slotvar)

class CallTemplateTag(DTTag):
    """
    """
    def __init__(self):
        DTTag.__init__(self,
                       'calltemplate',
                       isempty=1,
                       modules=[SkunkWeb, computils, slotutils])

    def genCode(self, indent, codeout, tagreg, tag):
        tagDebug(indent, codeout, tag)
        args=tagCall(tag,
                     (('template', None),('slotmap', None)),
                     kwcol='kw')
        args=pyifyArgs(tag, args)
        kw=pyifyKWArgs(tag, args['kw'])
        # get template
        template=getTempName()
        codeout.write(indent, 'if %s is None:' % args['template'])
        codeout.write(indent+4, '%s=__h.slotutils.getTemplatePath()' % template)
        codeout.write(indent, 'else:')
        codeout.write(indent+4, '%s=%s' % (template, args['template']))

        mapvar=args['slotmap']
        if mapvar is None:
            mapvar='SLOTS'
        codeout.write(indent, 'try:')
        codeout.write(indent+4, mapvar)
        codeout.write(indent, "except NameError:")
        codeout.write(indent+4, "%s=__h.slotutils.getConfiguredSlots()" % mapvar)
        K=getTempName()
        g=getTempName()
        k='__k4023562'
        codeout.write(indent, "%s=globals()" % g)
        # assigning to k assures that it can be deleted later, as
        # if mapvar is empty, then the loop variable won't be initialized!
        codeout.write(indent, "%s=%s=0" % (k,K))
        codeout.write(indent, "for %s in %s:" % (k,mapvar))
        codeout.write(indent+4, "%s=%s.upper()" % (K, k))
        codeout.write(indent+4, "try:")
        codeout.write(indent+8, "%s[%s]=%s[%s]" % (mapvar, k,g,K))
        codeout.write(indent+4, "except KeyError:")
        codeout.write(indent+8, "pass")
        codeout.write(indent, "del %s, %s, %s" % (g, k, K))
        codeout.write(indent, "if %s: " % kw)
        codeout.write(indent+4,
                      '%s.update(%s)' % (mapvar, kw))
        codeout.write(indent, "__h.OUTPUT.write(__h.computils.include(%s))" % template)
        codeout.write(indent, 'del %s' % template)
        

tagRegistry.addTag(SlotTag())
tagRegistry.addTag(CallTemplateTag())

    
__all__=('SlotTag','CallTemplateTag')
