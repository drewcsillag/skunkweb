import sys
import os

files = filter(lambda x:x[-5:]=='.html' and x[:4] != 'code', os.listdir(sys.argv[1]))

def compare(x, y):
    x = x[:-5]; lx = len(x)
    y = y[:-5]; ly = len(y)
    if x[:ly] == ly:   # if y is a prefix of x
        return -1
    elif y[:lx] == lx: # if x is a prefix of y
        return 1
    return cmp(x, y)

files.sort(compare)
    
for i in files: print i


