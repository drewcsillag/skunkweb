# Time-stamp: <02/02/24 10:40:39 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

########################################################################
# you need Rich Salz's excellent wizard.py for this, the original
# source for which is available at:
#
# http://www.zolera.com/resources/opensrc/wizard
#
# This is coded to work with wizard 2.0.
########################################################################

from wizard import *
import Tkinter as Tk
import productmaker
import traceback
import cStringIO

class _productHelp(HelpPopup):
    def __init__(self, helpdict):
        HelpPopup.__init__(self)
        self.helpdict=helpdict
    def open(self, wizard, field):
        self.text=self.helpdict.get(field)
    def readline(self):
        if self.text:
            t=self.text
            self.text=None
            return t
    def close(self):
        pass

_productHelpDict={
    'product_name': "the name of the product you wish to create.",
    'version': 'a version number of the product, such as 1.10.2.',
    'author' : 'the authors of the product.',
    'docroot': """the directory on your machine in which the SkunkWeb
components for this product reside.""",
    'libs' : """the directory on your machine in which the python modules
    (including SkunkWeb services) for this product reside.""",
    'format' : "The desired format for this product (zip, tgz, or tar)",
    'sheet0': 'Enter the name of your new product.',
    'sheet1' : '',
    'sheet2' : ''}

class _sheetchanger:
    def __init__(self):
        self.text=''
    def goto(self, wizard, sheetnum):
        if sheetnum==2:
            
            try:
                ppath=_makeProduct(wizard.get_values())
                wizard.bBack['state']=Tk.DISABLED
                self.text="Your new product was saved as:\n\n %s" % ppath
            except:
                sio=cStringIO.StringIO()
                traceback.print_exc(file=sio)
                self.text="Sorry, an error occurred:\n%s" % sio.getvalue()
    def open(self, wizard):
        pass
    def readline(self):
        if self.text:
            t=self.text[:]
            self.text=''
            return t
    def close(self):
        pass
            
def _get_wizard(root=None):
    builder=_sheetchanger()
    sheets=[Sheet(None,
                  (EntryField('product_name',
                              'Product Name',
                              entrywidth=50,
                              validate=Nonblank('product name')),)),
            Sheet(None, (EntryField('version',
                                    'Version',
                                    entrywidth=10,
                                    validate=Nonblank('version')),
                         EntryField('author',
                                    'Authors',
                                    entrywidth=20),
                         DirField('docroot',
                                  'Document sources',
                                  validate=Nonblank('docroot')),
                         DirField('libs',
                                  'Module sources'),
                         DDField('format',
                                 'Product format',
                                 ['.zip', '.tgz', '.tar']))),
            Sheet(None, (EntryField('services',
                                    'Services',
                                    entrywidth=40),
                         EntryField('dependencies',
                                    'Dependencies',
                                    entrywidth=40))),
            DynamicSheet(None, builder)]
    w=Wizard(sheets,
             'SkunkWeb Product Wizard',
             root,
             whenvalidate=1,
             sheetchange=builder)
    #help=_productHelp(_productHelpDict))
    return w

def _popdict(d, k, lenient=0):
    if d.has_key(k):
        v=d[k]
        del d[k]
        return v
    elif lenient:
        return None
    
def _makeProduct(data):
    productName=_popdict(data, 'product_name')
    docsources=_popdict(data, 'docroot')
    libsources=_popdict(data, 'libs', 1)
    format=('zip', 'tgz', 'tar')[int(_popdict(data, 'format'))]
    productFile=_popdict(data, 'productFile', 1)
    productPath=productmaker.makeProduct(productName,
                                         docsources,
                                         libsources,
                                         data,
                                         format=format,
                                         productFile=productFile)
    
    return productPath

_skunkguin="""
R0lGODlhpgCaAIQAAMDAwKCgoICAgFBQUAAAADAwMHBwcLCwsB8fHw8QD2NjY9DQ0PDw8ODg4I6O
jkBAQP///8/Pz////////////////////////////////////////////////////////yH+FUNy
ZWF0ZWQgd2l0aCBUaGUgR0lNUAAh+QQBCgAfACwAAAAApgCaAAAF/uAnjmRpnmiqrmzrpgvzznRt
33iOLo7yJISgMPgYCA4NnXLJbNoYgQFwSK0GEYqDzMntem0AxRArCAAEYqt1EPi63/BAQThwNCCQ
RkCBUPsJCQZJcISFNwB9BA8BDHgHBol/kkEDAIaXmDsPRAB4EAJTk6JCD5aZp4UMBkEJB54HkaOy
RIOotlyIlI0QEZuzv0MGW7fEOA0DQg6eAsBDDwplANLSAQZzVQltxdsvDWmAAXgMvr91EZ7o6XkO
sbTc7zChCecQDNeyi7vq++gA5KwO4NEAEECAwYPSnCyQR8/erFL8Iu7zR2XAMIEookwqYOCADgaR
5nn6NgmBK4ko/tUBuAdoAcYTAdpNSqDApQ1kQsLhcSDLYsqf6pgN0fbywwKWwAbUcnFgiDI8DUJJ
egq0qqcILA0UBSC1WZCALkDSQffPTyuraD0xIKkAYwCvatq2EEoAgb6mM+ml3cszJ7yFcOOyYBCq
kyeZ2PTu3RsglMdtYgMLVrEqiAF0bycZXsw5wpQES21Vlqzm8YkGQuyiQ0xFJ+fXnokUQ03a7EUS
31xDyPznMloGBwQM+EGlwIOO+iTGJgDWFsnaVZqTIEwkHWshBawycIBUUgE7KAGwun2JNnQ1CE7Q
3bxbEmigawMvkihUgK2+59XYHEG9rvWpQDnQlVcI6PZfAuQV/lJWfkOVgB9V7f3xwE8M4HSeSRMF
Yd8pDPqx4QiR3HGYJCJK5FCHipToCTIJnCIeilV8+AFeBGTnCW9q2IjSgvmdhQ5tphmCH4xCyEiX
b/UMSIUAKdFFJAFMorPKAJk4CQxxosglgoWuWWkFe/uY92QQCqBDXYJuPJfAAFIAKM4Bz1XxAAnk
GNbfHynxSGSZyxBAlIJD+FRPnEKclA6OctIphGFeVqEjPxGMaQWShGkJaBAFJAcBYnzuQ6hsI9SZ
h5JUdMrPp2N22eIl5Bh6oxUqpiNmFSSM1gmqQ0TJDwOSqvFeHgTsRwg59TjwgACN8FqRJ2cYVGJ3
QpCw3qx+/riqDqK9krLin3BUlt09A+CBVJR4PbCJTkNSQQJve4wCZjrQZuvnTpbCIdQDkSoiXidl
GZYIAhDwdEe+X47wIgEKkFqFpmbKix4e/lxy78ENYAFBv7zkCgFzePhhigjNSIStw0GEI57ErJhn
gLkXU9HJwUFEgMBTpEp3na8S4ZotwOKF5gZdm7KCwISjaQgBzIuKq4aMFo4yYUQ3yxvBvoash6Ou
eETgQCfUEuCJH1SO0Ogf4fLTNcmWiSfdG0fuBkRHHXligAL0PFc2wYka/Mu7r6JtBQLiyfjGwQhy
5UqB6QCwmZPZrGRWCXtHVLTfQxGgVSEwI4CAYig1IEDU/kNcpKcafOMxOtrIzIn5EAXEClQEkGgm
7SylQ6Aw5aoTcnDZrznuIQlIS1L62ZSDqrsQDO9FPAFhj3A7Fa5DXLwfucOh7NOvff24oqNElO70
pFyS8mINPAOVJMKObUVE6hffPCFCJIB1gEA80MjIwQAvS0SnUy74G1RAEkpgl4BAlKhpVljVCPbH
j3hNj1sAdJlyYscGdYhCRg6kQkTAp59LdEcAJWIAABzQJvmJyAEO0IcoEDSCyflhVxysQnpYJQv5
7QIr1elYlkZAI0nwI3gcrBccFjQ3cxnxCGopmmqCJgqbLA87P4whFYJEiES0SRHJw0NjSMEeF6oh
d6DD/l46vsdBNHmBN4qLH+d2ExIDJWkU2tCZIvjRPr8pkBB3woOTFGCGasTCfvwgYwJlgD9nnEqK
4TMEOfh0J19BaB8I9ENbFjAJMZIFOoE4wAgT5pU7vmFIm1mOFQqwRnVERnbPs6Qn+jcKBdyGAaBo
RiEoCUV04LAKAgzPKNIjSG3t43kXTEGFgFEIlrjxE/EDIVpYqSEgGnIfpHkfCnqpBp9xwUkAg1QF
9+JMK+hMlToMjHGgEQ3yAMZdb6Bl0rIHtVlcB5wbwyQbhEWCc07if05gCTzZuRN3enGO+wDdJNjQ
ghNJonrXnCI/I/LEKjQAWvBkph8EMQOD/sGaSlAn/isWKhGB5gRviYgoXBAalgxSwgtI2SdH/6mG
cNVHKI+6pFc+RgOLki6hS+JoRHpIBLOIyy684QdLD5oDm+aNCRotklWCU0oTVUEBDgxHBM5xMDp6
hZ41MKrLmsCj+UlkAJrDolUWVMhsas9r+2AcMBG2BK2mhgn48yod+cQTH/0EWw/opW4SYVU6iNJX
GLXBUPFZU1Llclc6ygXCoreP7mjECmL0Bd9gpoyhQgkXqMIqDVj6yH0YwEfla81PgmcX1mymMpMd
wlTdY8aiRqErdsFBUseQxVcA4YTdqa1Mc+VM7AkltYV6nhC70IDgPGAOBcDB6GpXj9HohFCMTQfe
/sbzT8Pkq3S/0GxRPlDIw/YjFkwaRxV4l5I4lQlandqEXFs2iuRu1wSnpAKCGDo5JgUvU1XpWgOm
KwQRRWq9dczVe02gvmOio2kisZJ3URInl3pzJOvtZhW0WxTWzJd9YP0KL5oGkbR0DQDx7S9U1htP
UQy4BIUkMR4QUBllWKmzY5VThEqlFv6RqZckfe/ooouH4czrOTC2ysgYMcgmZeNo1DMBACh8i26S
lx9bBMB0L8wZZeU0klBKSQNO+Lvp5HgbqLIWP9RrOyqwWAuc6c6EyEjllLC0XgTFCPHMihLxTpVU
zP2qDJFsBRXDK8k8ZCFG1LdgKBdAABF4TgGq/rGYRoXTzEB54jCw8JJGUqGpIlOAAoqIAGTlodFW
OIcfDJyOOm6oKUy2BW/WNIQE9A4APK4KEDvBGjq38w8JiEEBZoiRSMTOlzpdDBDDMTpSn28mb3sJ
zJDm52BLBIhMkhBKqDnhl/wDacZ29rP7XGI17KiGLxFTAZCWZ21HMUaSjoiVRfFlYhTtATzFtLkj
Am0JE6B2hZzUS/SZrnmnBdp1rB2W/bA2blChFBr0t1WAeID+BbmhWxVI8Kar8IVjo9tL66ssXuIl
mQ2h4rKOjr2zHNBZSJMbkXSAk0AOFKSVib8x2ke+rVDwbQwIYPdg+WgpcQC9QOE6cvVof+Ws/oYU
XkPnWoZ3+YpgEDP4rgpunPlR4eHMeayl2UjvceTMtNYGYWTdxdFt1n8EjFgN3A+8FkhTOrxFTIl9
7BCQI6TRQW0rQJAbYtCNQQEH90MNpwhdF4IALQvZ7QKBYSQRRt/jLhkRDfMXmSrK2vdhURuOnUaV
GLloYRl4weuYY5RvhwmRngYbaV4IdDu7hFJNjBfV9q+ol7dOfUEPiJNJj78oxYDF8uRrUa/c7NyE
qZgJobqTiaZFOUoQyo2rDpt7E4qBvXwNZNnvtJYYUDAIOVSqFpPi6/loxYwfSKmOTaj87+YyQAAC
yw17qvZ1F3R2aCci+vVu4vrb3UQrIhFk/o3/wVTs5DmbwFgFYQBIJDkEQEUntkD3BgEHkAAFIGZ5
IgrZZhXQsAnAJzJstYAl8CIBCEwxxRmoIQAYmD20wX5bEQSx9hPGt1DMQIKg9xp9EHkcyIBYN4E+
xE7UAYM3KBGVMVwD1gdtRj7uwU/1sQmFll+oh3/wkAYV+BPtA4CLkQgwyH1AQQ4FwHrvUC4L5UAZ
qBxFsglW2HLfQFhfJwQLBXOWs1AN8FkP0AdjWBWw1AcIoIXFsE7s5CUhyBdFMEK+EIdoAQqtcGJ4
yE4s4UrZc0sxw4XO9h0FIGjbJWJpeAUSGIhPFU+AKIeUwBzvRUu2xk6rQA8RsIL7oIiG/pRDOlUu
l7VdfdF/i0EY+PUDT4gOhIaJzjYlQGCHqDAHQ2iECMN48zJaN4MEqMhRfuQnnahhzqYsWnANnkZv
rMRnmUghzAA4A5YZUrhQYoAgJzIznKM1ArVmaMiGnCQMJ0YbvchP2MhnrPOGv8AkdCF7KbEd12AS
NVgZs4gWBHMHQvcH/FIor2gsycSETQgI8rgXgsdejcdEJIcWDziQNVgC25iP8AFFEpWDzySHFlIg
EYkCaSAo/AQzDBkYDZA5ViEgANGRKXAPlsdO+FEg0KEA6fJ2ebBIBLmACxALNPGFDYQdnbd1EoGS
gIB8KpkRanYENGlL8uKKj4dFRfkCpcABg8WBHPOIFGcGYjnwdJTAWA9JJk+JA2fQHRyBZurwUIGi
iy3QNUPTdAXxD0D4lTPQANwxSgawNZskDwq4BAFWKnDZBAvASaJAg13gVt7Ul1wABSb1lkhlUhpi
mF+wAL+2JKnwOdSDlo5pAwtAgumHgl2wAAVxEEfAmZc5mqRZmqZ5mqipO6m5mtLCmq5phq55mbAZ
m4Y5m7QJl7Z5m7q5mwMWAgA7
""".strip()

def main():
    title='SkunkWeb Product Wizard'
    root=Tk.Tk()
    root.title(title)
    root.iconname(title)    
    fr1=Tk.Frame(root)
    imageholder=Tk.Label(fr1)
    pi=Tk.PhotoImage(data=_skunkguin)
    imageholder['image']=pi
    imageholder.grid()
    fr1.grid(row=0, column=0)
    fr2=Tk.Frame(root)
    fr2.grid(row=0, column=1)
    w=_get_wizard(fr2)
    return w.run()

if __name__=='__main__':

    main()
             
