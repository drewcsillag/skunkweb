import sys
text="this that <<:val `foo`:> other"

import DTLexer

rv = DTLexer.findTags(text)
print rv
if len(rv) != 3:
    print " should've found a tag"
    sys.exit(1)
else:
    print "passed"
    sys.exit(0)
