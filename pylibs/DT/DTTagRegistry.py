#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""The tag registry.  If you want to add a new tag, you use one of these.
It's really just a fancy looking dictionary"""
import string
import UserDict

import DTTags
from SkunkExcept import *

class DTTagRegistry(UserDict.UserDict):
    def __init__(self, tags = None):
        UserDict.UserDict.__init__ ( self, tags )

    def addTag(self, dttag):
        """
        Add a tag
        """
        if self.data.has_key ( dttag.tagname ):
            raise SkunkStandardError, "tag '%s' already exists!" % dttag.tagname

        self.data[dttag.tagname]=dttag

    def removeTag(self, tagname):
        """
        Clear a tag
        """
        if self.data.has_key ( tagname ):
            del self.data[tagname]

    def getTag(self, tagname):
        try:
            return self.data[str(tagname)]
        except KeyError:
            raise KeyError, "Tag named '%s' not a valid tag - %s" % (
                tagname, self.keys())

    def __str__(self):
        return '<DTTagRegistry: ['+string.join(self.data.keys(),', ')+']>'

# Return the default tag registry. 
# Note that a new object is returned each time the function is called
def get_standard_tags():
    import DTTags
    tr=DTTagRegistry()

    tr.addTag ( DTTags.ForTag () ) 

    tr.addTag(DTTags.ValTag() )
    tr.addTag(DTTags.DelTag() )
    tr.addTag(DTTags.CallTag() )
    tr.addTag(DTTags.ContinueTag() )
    tr.addTag(DTTags.BreakTag() )

    # VarDict
    tr.addTag(DTTags.VardictTag() )

    # Bool
    tr.addTag(DTTags.BoolTag() )

    # Checked tag
    tr.addTag(DTTags.BoolTag('checked', def_true = 'checked' ))
    tr.addTag(DTTags.BoolTag('selected', def_true = 'selected' ))

    # If / While
    tr.addTag ( DTTags.IfTag() )
    tr.addTag ( DTTags.WhileTag() )

    tr.addTag(DTTags.ElseTag() )
    tr.addTag(DTTags.ElifTag() )

    # Add both full and brief comment tags
    tr.addTag(DTTags.FullCommentTag() )
    tr.addTag(DTTags.BriefCommentTag() )

    tr.addTag(DTTags.RaiseTag() )
    tr.addTag(DTTags.TryTag() )
    tr.addTag(DTTags.ExceptTag() )
    tr.addTag(DTTags.FinallyTag() )

    tr.addTag(DTTags.DefaultTag() )
    tr.addTag(DTTags.HaltTag() )
    tr.addTag(DTTags.SpoolTag() )
    tr.addTag(DTTags.ImportTag() )
    tr.addTag(DTTags.SetTag() )
    tr.addTag(DTTags.DocTag() )
    #tr.addTag(DTTags.DUMMY)

    return tr
