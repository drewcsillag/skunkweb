from DT.DTTags import SpoolTag
from DT import DTCompilerUtil
import SkunkWeb.Configuration as C
#from SkunkWeb.LogObj import DEBUG
#from SkunkWeb.ServiceRegistry import USER

class SafeSpoolTag(SpoolTag):
    _attend_to_comments=1

    def _pushCommentLevel(self, indent, codeout, val):
        codeout.write(indent, "__t.SkunkWeb=__import__('SkunkWeb')")
        oldvalname=DTCompilerUtil.getTempName()
        codeout.write(indent, "%s=__t.SkunkWeb.Configuration.componentCommentLevel" % oldvalname)
        codeout.write(indent, "__t.SkunkWeb.Configuration.componentCommentLevel=int(%s)" % val)
        return (oldvalname,)

    def _popCommentLevel(self, indent, codeout, oldvalname):
        codeout.write(indent, "__t.SkunkWeb.Configuration.componentCommentLevel=%s" % oldvalname)
        codeout.write(indent, "del %s" % oldvalname)

    def _testCommentLevel(self, indent, codeout, commentLevel):
        codeout.write(indent, "if int(%s) not in (0, 1, 2, 3):" % commentLevel)
        codeout.write(indent+4, "raise ValueError, \"unrecognized value: %s\"" % commentLevel)

            
        


