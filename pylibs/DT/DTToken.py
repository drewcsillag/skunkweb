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

class DTToken:
    """an easier to use (and debug) wrapper around the taglist that
    TextTools spews back"""
    def __init__(self, tag, text):
        self.tag=tag
        self.text=text

    def __repr__(self):
        return "<Tag %s:%s>" % (self.tagname(),repr(str(self)))

    def __str__(self):
        """given a tag and the source text, produces the text of the tag"""
        try:
            return self.text[self.tag[1]:self.tag[2]]
        except TypeError:
            print tag[1], tag[2]
            
    def __len__(self):
        if self.tag[3] is not None:
            return len(self.tag[3])
        return 0

    def __getitem__(self, item):
        try:
            return DTToken(self.tag[3][item], self.text)
        except AttributeError:
            raise IndexError

    def children_p(self):
        return not (not self.tag[3])

    def start(self):
        return self.tag[1]

    def end(self):
        return self.tag[2]
    
    def tagname(self):
        return self.tag[0]

    def __getslice__(self, s, e):
        ntag=self.tag[:3]+(self.tag[3][s:e],)
        return Tag(self.tag[:3]+(self.tag[3][s:e],), self.text)
        
class LazyDTTokenList:
    """a lazily evaluated list of tokens.  Only produces tokens as needed
    (as opposed to doing them in batch).  Not sure this buys us much, but
    it might (then again, we might be losing some too)."""
    
    def __init__(self, taglist, text):
        self._taglist=taglist
        self._text=text
        
    def getTagList(self):
        return self._taglist
    
    def __getitem__(self, item):
        return DTToken(self._taglist[item], self._text)

    def __getslice__(self, b, e):
        return LazyDTTokenList(self._taglist[b:e], self._text)

    def __len__(self):
        return len(self._taglist)

    def __repr__(self):
        tags=map(repr, self)
        return '['+string.join(tags,', ')+']'

if __name__=="__main__":
    import sys
    import DTLexer
    import DTUtil
    tl=DTLexer.doTag(open(sys.argv[1]).read())
    for i in tl:
        print '--------------------'
        print '%s:%s:%s' % (len(i), i.tagname(), i)
        for j in i:
            print '%s:%s:%s' % (len(j), j.tagname(), j)
            if len(j) > 1:
                for k in j:
                    print '%s:%s:%s' % (len(k), k.tagname(), k)
        print DTUtil.tagattrToTupleDict(i)
