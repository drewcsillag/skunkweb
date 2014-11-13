# Time-stamp: <2002-01-22 11:08:19 drew>

######################################################################## 
#  Copyright (C) 2001 Andrew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

import string
import struct

def _checksum(ck, contents):
    sum = 0L
    for i in contents:
        sum += 0xFFL & ord(i)
        
    for i in contents[148:156]:  #treat checksum bytes as spaces
        sum -= 0xFFL & ord(i)
        sum += ord(' ')

    return sum == ck

def _cvtnulloctal(f, k=None):
    zi = f.find('\0')
    if zi > -1:
        f = f[:zi]
    try:
        return string.atoi(f, 8)
    except:
        return 0

def _tarstr(f):
    zi = f.find('\0')
    if zi > -1:
        f = f[:zi]
    return f

def _tf(name, *args):
    print name

def readTar(fileObj, tarEater=_tf):
    """Read through the contents of a tar archive

    fileObj is a file (or file-like) object
    tarEater is a callable object which takes the following arguments:
        name, contents, size, mode, uid, gid, mtime
        typeflag, linkname, uname, gname, devmaj, devmin
    """
    while 1:
        header = fileObj.read(512)
        if len(header) != 512:
            raise EOFError, 'Unexpected end of tar stream'

        (name, mode, uid, gid, size, mtime, cksum, typeflag,
         linkname, ustar_p, ustar_vsn, uname, gname, devmaj,
         devmin, prefix) = struct.unpack(
            '100s8s8s8s12s12s8s1s100s6s6s32s32s8s8s155s', header[:504])

        name, linkname, uname, gname, prefix = map(_tarstr, (
            name, linkname, uname, gname, prefix))

        mode, uid, gid, size, mtime, cksum, devmaj, devmin = map(
            _cvtnulloctal, (mode, uid, gid, size, mtime, cksum, devmaj,
                            devmin))
        if name:
            try:  
                typeflag = {
                    '': 'regular',
                    '0': 'regular',
                    '\0': 'regular',
                    '1': 'link',
                    '2': 'symbolic link',
                    '3': 'character special',
                    '4': 'block special',
                    '5': 'directory',
                    '6': 'fifo',
                    '7': 'reserved',
                    }[typeflag]
            except:
                raise KeyError, 'unknown file type in tar %X <%s> ' % (ord(typeflag), name)
            
        blocks_to_read = size / 512
        if size - (blocks_to_read * 512):
            blocks_to_read += 1
        contents = fileObj.read(blocks_to_read * 512)
        contents = contents[:size]

        if prefix:
            name = prefix + name 
        if name:
            ecount = 0
        else:
            ecount += 1
        if ecount == 2:
            break
        
        if name: #null name fields are normal in tar files, so have to check
            #here you would do whatever you wanted with the information
            #in: name, linkname, uname, gname, mode, uid,gid,size,mtime,devmaj
            #devmin, contents
            if not _checksum(cksum, header):
                raise ValueError, "checksum error -- %s" % name

            tarEater(name, contents, size, mode, uid, gid, mtime, 
                     typeflag, linkname, uname, gname, devmaj, devmin)
            
             

if __name__ == '__main__':
    import gzip, sys
    if sys.argv[1][-2:] == 'gz':
        readTar(gzip.GzipFile(sys.argv[1]))
    else:
        readTar(open(sys.argv[1]))
    
