from DT.DTTags import SpoolTag
from DT import DTCompilerUtil
import SkunkWeb.Configuration as C
from SkunkWeb.LogObj import DEBUG
from SkunkWeb.ServiceRegistry import USER

class SafeSpoolTag(SpoolTag):
    _attend_to_comments=1

    def genCode(self, indent, codeout, tagreg, node, meta):
        DEBUG(USER, "component comment level is %s" % C.componentCommentLevel)
        SpoolTag.genCode(self, indent, codeout, tagreg, node, meta)
        

    def _pushCommentLevel(self, indent, codeout, val):
        val=int(val)
        oldvalname=DTCompilerUtil.getTempName()
        codeout.write(indent, "import SkunkWeb.Configuration")
        codeout.write(indent, "%s=SkunkWeb.Configuration.componentCommentLevel" % oldvalname)
        codeout.write(indent, "SkunkWeb.Configuration.componentCommentLevel=%s" % val)
        return (oldvalname,)

    def _popCommentLevel(self, indent, codeout, oldvalname):
        codeout.write(indent, "SkunkWeb.Configuration.componentCommentLevel=%s" % oldvalname)
        codeout.write(indent, "del %s" % oldvalname)

    def _testCommentLevel(self, indent, codeout, commentLevel):
        if commentLevel not in (0, 1, 2, 3, "0", "1", "2", "3"):
            codeout.write(indent, "raise ValueError, \"unrecognized value: %s\"" % commentLevel)

            
        


