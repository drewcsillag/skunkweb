import mmap
import os
import tempfile
import struct

class mmint(object):
    """
    an object whose ival attribute contains a memory-mapped integer value.
    """
    def __init__(self, ival=0):
        fname=tempfile.mktemp()
        f=file(fname, 'w+')
        os.unlink(fname)
        f.write(struct.pack('i', 0))
        f.seek(0)
        self._mm=mmap.mmap(f.fileno(), 4)
        if ival:
            self._set_ival(ival)

    def _get_ival(self):
        self._mm.seek(0)
        return int(struct.unpack('i', self._mm.read(4))[0])

    def _set_ival(self, ival):
        ival=int(ival)
        self._mm.seek(0)
        self._mm.write(struct.pack('i', ival))

    ival=property(_get_ival, _set_ival)

    def __int__(self):
        return self._get_ival()
        
def _test():
    import random, time, sys
    def child():
        try:
            while 1:
                time.sleep(0.45)
                mi.ival=random.randint(0, 10000)
        except KeyboardInterrupt:
            sys.exit(0)
	    
    def parent():
        try:
            while 1:
                time.sleep(0.5)
                print mi.ival
        except KeyboardInterrupt:
            sys.exit(0)

    mi=mmint()
    if os.fork():
        parent()
    else:
        child()


__all__=['mmint']

if __name__=='__main__':
    print "Stop this with Control-C when you've been sufficiently entertained."
    _test()
