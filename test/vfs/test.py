import vfs
import vfs.importer as importer
import traceback
import sys


def do_imports():
    try:
        import orangutan
        print orangutan.FOO
        print dir(orangutan)
    except ImportError:
        traceback.print_exc()

    try:
        import hamster.droppings
        print hamster.droppings.FOO
        print dir(hamster)
        print dir(hamster.droppings)
    except ImportError:
        traceback.print_exc()

    try:
        import hamster.snarl
        print hamster.snarl.FOO
        print dir(hamster.snarl)
    except ImportError:
        traceback.print_exc()

    try:
        import gerbil.droppings
        print gerbil.droppings.FOO
        print dir(gerbil)
        print dir(gerbil.droppings)
    except ImportError:
        traceback.print_exc()

    try:
        import gerbil.snarl
        print gerbil.snarl.FOO
        print dir(gerbil.snarl)
    except ImportError:
        traceback.print_exc()


def test_zip():
    vfsurl="vfs://<ziptest>/libs"
    sys.path.append(vfsurl)
    vfs.VFSRegistry['ziptest']=vfs.ZipFS('/home/smulloni/workdir/skunkweb/test/vfs/libs.zip')
    importer.install()
    do_imports()
    importer.uninstall()


def test_local():
    vfsurl="vfs://<localtest>/home/smulloni/workdir/skunkweb/test/vfs/libs"
    sys.path.append(vfsurl)
    vfs.VFSRegistry['localtest']=vfs.LocalFS()
    importer.install()
    do_imports()
    importer.uninstall()


if __name__=='__main__':
    if len(sys.argv)==1:
        action='local'
    else:
        action=sys.argv[1]
    if action=='zip':
        test_zip()
    elif action=='local':
        test_local()
    else:
        print >> sys.stderr, "unknown action"
