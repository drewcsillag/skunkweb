from DT.DTTags import SpoolTag
from DT import DTCompilerUtil
import SkunkWeb.Configuration as C

class SafeSpoolTag(SpoolTag):
    _attend_to_comments=1

    def _pushCommentLevel(self, indent, codeout, val):
        Cfg=DTCompilerUtil.safe_import(indent, codeout, 'SkunkWeb.Configuration')
        oldvalname=DTCompilerUtil.getTempName()
        codeout.write(indent, "%s=%s.componentCommentLevel" % (oldvalname, Cfg))
        codeout.write(indent, "%s.componentCommentLevel=int(%s)" % (Cfg, val))
        return (oldvalname,)

    def _popCommentLevel(self, indent, codeout, oldvalname):
        s="__h.SkunkWeb.Configuration.componentCommentLevel"
        lines=((indent,
                "%s=%s" % (s, oldvalname)),
               (indent,
                "del %s" % oldvalname))
        codeout.writelines(*lines)

    def _testCommentLevel(self, indent, codeout, commentLevel):
        lines=((indent,
                "if not (0 <= int(%s) <=3):" % commentLevel),
               (indent+4,
                "raise ValueError, \"unrecognized value: %s\"" % commentLevel))
        codeout.writelines(*lines)

            
        


