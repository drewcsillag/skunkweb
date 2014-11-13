from computils import current_component, datacomp
from SkunkWeb import Configuration as C
from SkunkWeb.LogObj import logException
from vfs import FileNotFoundException, VFSException
from os.path import join as pathjoin

C.mergeDefaults(slotConfigFilename='slotconf.pydcmp',
                defaultTemplateFilename='template.comp')

# require the context service
import mvc.services.context

def templatize(callback=None,
               template=None):
    """
    invokes the layout templating mechanism; slots
    can be further configured by setting a callback
    """
    conn=SkunkWeb.Context.connection
    conn.setContentType('text/html')
    slots=getConfiguredSlots(path=conn.uri)
    if callback:
        callback(slots,conn)
    return stringcomp(getTemplatePath(template=template),
                      SLOTS=slots)

def getTemplatePath(template=None):
    """
    returns the path of the template
    """
    if template is None:
        template=C.defaultTemplateFilename
    return getSkinComponentPath(template)

def getSkinComponentPath(compname):
    """
    returns the path of a component in the current skin
    """
    return pathjoin(C.skinDir, C.defaultSkin, compname)

def getConfiguredSlots(path=None, slotfilename=None):
    """
    get the slots configured for given path.
    """
    if path is None:
        path=current_component()
    if slotfilename is None:
        slotfilename=C.slotConfigFilename
    elif not path.endswith('/'):
        path=path+'/'
    slots={}
    conffiles=[pathjoin(path[:(x or 1)], slotfilename) \
               for x, y in enumerate(path) if y=='/']
        
    for c in conffiles:
        try:
            newslots=datacomp(c, path=path)
        except FileNotFoundException:
            continue
        except VFSException:
            logException()
            continue
        else:
            slots.update(newslots)
    return slots

__all__=['getConfiguredSlots',
         'getTemplatePath',
         'getSkinComponentPath',
         'templatize']
