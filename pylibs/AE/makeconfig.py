#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import os

#find .py files whose first letter in name isn't .
files = [ i
          for i in os.listdir('.')
          if len(i)>3 and i[-3:] == '.py' and i[0] != '.'
]
cfglines = []

#find configuration stuff
off = 1
for i in files:
    for j in open(i).readlines():
        if not off:
            if j[:8] == '#/config':
                off = 1
                continue
            cfglines.append( ( i, j ) )
        if off and j[:7] == '#config':
            off = 0

d = {}
mods = []
for i in cfglines:
    fname = i[0][:-3]
    if fname not in mods:
        mods.append(fname)
    d[i[1].split()[0]] = fname

#find initialization stuff
initCalls = []
initMods = {}
for i in files:
    for j in open(i).readlines():
        if j[:14] == "#init funcs ==":
            initCalls.extend(
                ["%s.%s" % (i[:-3], fname) for fname in j[14:].split()])
            initMods[i[:-3]] = 1

#find initialization stuff
chldInitCalls = []
for i in files:
    for j in open(i).readlines():
        if j[:20] == "#child init funcs ==":
            chldInitCalls.extend(
                ["%s.%s" % (i[:-3], fname) for fname in j[20:].split()])
            initMods[i[:-3]] = 1

for m in mods:
    initMods[m] = 1
    
print """
%s

dict = {
%s
}


modules = {}

%s

def setConfigVar(name, value):
    mod = dict[name]
    setattr(modules[mod], name, value)

def setConfigVars(d):
    for k, v in d.items():
        setattr(modules[dict[k]], k, v)

def getConfigVar(name):
    mod = dict[name]
    return getattr(modules[mod], name)

def serverInit():
    pass
%s

def childInit():
    pass
%s
""" % ("\n".join(["import %s" % im for im in initMods.keys()]),
       "\n".join(["    '%s': '%s'," % i for i in d.items()]),
       "\n".join(["modules['%s'] = %s" % (i, i) for i in mods]),
#       mods,
       "\n".join(["    %s" % ic for ic in initCalls]),
       "\n".join(["    %s" % ic for ic in chldInitCalls])

       )




