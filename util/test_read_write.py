#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#!/usr/local/bin/python
#
# Test the writing & reading
#
# Roman, Starmedia, 2000

import time, os, commands, stat, cPickle

print "--> This is a python disk performance benchmarking tool"
_sysname = commands.getstatusoutput ( 'uname -a' )[1]
print '--> System: %s' % _sysname

_file1, _file2 = 'test_file1', 'test_file2'

# Create a dictionary result, in case we will want to collate them together
_outfile = 'result.dict'

def do_bench ( fsize ):
    """
    Do all of the benchmarks for the given file size
    """

    _res = {}

    print '--> Testing file size: %d bytes (%.1fk)' % ( fsize, float(fsize) 
                                                               / 1024 )

    data = '0' * fsize

    _time = time.time()
    _count = 1000

    for i in range ( 0, _count ):
        f = open ( _file1, 'w' )
        f.write ( data )
        f.close()

    print 'Done %d writes, avg time %.5fs' % \
                               (_count, (time.time() - _time)/_count)

    _res['write'] = (time.time() - _time)/_count

    _time = time.time()
    for i in range ( 0, _count / 2 ):
        os.rename ( _file1, _file2 )
        os.rename ( _file2, _file1 )

    print 'Done %d renames, avg time %.5fs' % \
                               (_count, (time.time() - _time)/_count)

    _res['rename'] = (time.time() - _time)/_count

    _time = time.time()

    for i in range ( 0, _count ):
        f = open ( _file1, 'w' )
        f.write ( data )
        f.close()
        os.rename ( _file1, _file2 )

    print 'Done %d writes & renames, avg time %.5fs' % \
                               (_count, (time.time() - _time)/_count)


    _res['write_rename'] = (time.time() - _time)/_count

    _time = time.time()

    for i in range ( 0, _count ):
        f = open ( _file2, 'r' )
        f.read()
        f.close()

    print 'Done %d reads, avg time %.5fs' % \
                               (_count, (time.time() - _time)/_count)

    _res['read'] = (time.time() - _time)/_count

    _count = 10000
    _time = time.time()

    for i in range ( 0, _count ):
        data = os.stat ( _file2 )[stat.ST_MTIME]

    print 'Done %d stats, avg time %.6fs' % \
           (_count, (time.time() - _time)/_count)

    _res['stat'] = (time.time() - _time)/_count

    return _res

#
# Ok, do the tests
#
_fsizes = map ( lambda x : 512 * 2**x, range (0, 9) )

_tot_time = time.time()
_res = {}

for size in _fsizes:
    try:
        _time = time.time()
        _res[size] = do_bench(size)
        _res[size]['total'] = time.time() - _time
    finally:
        # Cleanup
        try:
            os.unlink ( _file2 )
        except:
            pass

        try:
            os.unlink ( _file1 )
        except:
            pass

print '--> Total bench time: %.4f' % (time.time() - _tot_time)

# Now, create the pickled file with the results
# Contains a tuple : ( sysname, totaltime, { fsize: {result}, ...} )
data = ( _sysname, (time.time() - _tot_time), _res )

cPickle.dump ( data, open ( _outfile, 'w' ), 1 )

print '--> Dumped test results to %s' % _outfile
