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




