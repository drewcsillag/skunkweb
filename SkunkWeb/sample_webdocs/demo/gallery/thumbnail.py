# doing this in python is necessary because STML tends to introduce
# line returns, being an embedded format; something about STML we
# might fix someday.

import cStringIO
import os, sys
import AE.Component as C
import AE.Cache as Cache
import DT
import PIL.Image as Image

SUPPORTED_EXTENSIONS=[x[1:] for x in Image.EXTENSION.keys()]

globals().update(CONNECTION.extract_args('imagefile', x=150, y=150))
if not imagefile:
    raise NameError, "imagefile"

size=(int(x),int(y))

# the action. By delegating the thumbnail creation to a datacomponent,
# we are able to use the cache

mimetype, bytes=C.callComponent('comp/thumbnail.pydcmp',
                                {'imagefile' : imagefile,
                                 'size' : size},
                                cache=1,
                                compType=DT.DT_DATA)
CONNECTION.responseHeaders['content-type']=mimetype
sys.stdout.write(bytes)



