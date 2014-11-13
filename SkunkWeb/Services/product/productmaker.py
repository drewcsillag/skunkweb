# Time-stamp: <02/02/24 10:29:06 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
########################################################################

"""
a script which produces a product from sources.

REQUIREMENTS:

1. specify the location of the docroot.
2. specify the location of the libs.
3. byte-compile the libs, if any.
4. prompt for dependencies, services, product name,
   version, author, (etc.), format.
5. produce and save the archive file.

TODO:

* add error checking!
* add commandline script

"""
import compileall
import cStringIO
import os
import shutil
import sys
import zipfile
import gzip
import manifest

def _getbuildroot(builddir, productName):
    buildroot=os.path.join(builddir, productName)
    if os.path.exists(buildroot):
        incr=1
        while 1:
            br='%s.%d' % (buildroot, incr)
            if not os.path.exists(br):
                buildroot=br
                break
            incr+=1
    try:
        os.makedirs(buildroot)
    except:
        print >> sys.stderr,\
              "unable to create temporary build space at %s" % buildroot
        raise
    return buildroot

    
def makeProduct(productName,
                docsources,
                libsources,
                manifestData,
                format='zip',
                builddir='/tmp',
                comments=(),
                productFile=None):
    """
    given the necessary ingredients, builds the product archive
    and returns the path to it.
    """

    buildroot=_getbuildroot(builddir, productName)
    docroot=os.path.join(buildroot, manifestData.get('docroot', 'docroot'))
    libs=os.path.join(buildroot, manifestData.get('libs', 'libs'))
    shutil.copytree(docsources, docroot)
    if libsources:
        shutil.copytree(libsources, libs)
        # to silence the compileall module
        sys.stdout=cStringIO.StringIO()
        compileall.compile_dir(libs, force=1)
        sys.stdout=sys.__stdout__
    manifestpath=os.path.join(buildroot, manifest.MANIFEST_FILE)
    manifest.write_manifest(manifestpath, manifestData, comments=comments)
    
    if format=='zip':
        dest=productFile or os.path.join(builddir, '%s.zip' % productName)
        z=zipfile.ZipFile(dest,
                          mode='w',
                          compression=zipfile.ZIP_DEFLATED)
        def zipwalker(zippy, dirname, names, buildroot=buildroot):
            absd=os.path.join(buildroot, dirname)
            brlen=len(buildroot)
            for n in names:
                absn=os.path.join(dirname, n)
                reln=absn[brlen+1:]
                if os.path.isdir(absn):
                    pass
                else:
                    zippy.write(absn, reln)
        os.path.walk(buildroot, zipwalker, z)
        z.close()
        
    elif format in ('tar', 'tgz', 'tar.gz'):
        dest=os.path.join(builddir, '%s.tar' % productName)
        status=os.system('cd %s; tar cf %s *' % (buildroot, dest))
        if status:
            raise RuntimeError, "error creating tar file: %s.tar: %s" \
                  % (productName, status)
        
        if format=='tar':
            if productFile:
                if dest != productFile:
                    shutil.copyfile(dest, productFile)
                    os.unlink(dest)
                dest=productFile
        else:
            tf=open(dest)
            dest=productFile or os.path.join(builddir, '%s.%s' % \
                                             (productName, format))
            gf=gzip.open(dest, 'w')
            buffsize=2<<10
            while 1:
                stuff=tf.read(buffsize)
                if stuff:
                    gf.write(stuff)
                else:
                    break
            gf.close()
    shutil.rmtree(buildroot)
    return dest    
            
        
        

    


